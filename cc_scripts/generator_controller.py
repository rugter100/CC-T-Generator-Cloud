import time
import requests

from cc import peripheral

rpm_controller = peripheral.wrap("left")
l1_gauge_voltage = peripheral.wrap("bottom")
l2_gauge_voltage = peripheral.wrap("top")
remaining_gauges = peripheral.wrap("right")
target_voltage = 1600
url = '10.1.10.35:2062/submitdata'
gen_data = {"generator_id": 1}
shutdown = False
max_rpm = False
new_rpm = rpm_controller.getTargetSpeed()

def check_voltage():
    global new_rpm
    l1_voltage = float(str.split(l1_gauge_voltage.getLine(1), " ")[1])
    l2_voltage = float(str.split(l2_gauge_voltage.getLine(1), " ")[1])
    sum_voltage = l1_voltage + l2_voltage

    if sum_voltage >= 1625:
        volt_stability = 2
        print("high voltage detected!")
        print(f"L1:    {l1_voltage}V")
        print(f"L2:    {l2_voltage}V")
        print(f"L1+L2: {round(sum_voltage, 2)}V")

        voltage_offset = sum_voltage - target_voltage

        print(f"Voltage Offset: {round(voltage_offset, 2)}V")

        rpm_adjust = round((voltage_offset) / 20, 0)
        current_rpm = rpm_controller.getTargetSpeed()

        if rpm_adjust == 0:
            rpm_adjust = 1
        if current_rpm == 256:
            max_rpm = False

        print(f"Adjusting RPM from {current_rpm} RPM to {current_rpm - rpm_adjust} RPM")
        rpm_controller.setTargetSpeed(current_rpm - rpm_adjust)
        new_rpm = int(current_rpm - rpm_adjust)

    elif sum_voltage < 1600:
        volt_stability = 0
        print("low voltage detected!")
        print(f"L1:    {l1_voltage}V")
        print(f"L2:    {l2_voltage}V")
        print(f"L1+L2: {sum_voltage}V")

        voltage_offset = target_voltage - sum_voltage

        print(f"Voltage Offset: {round(voltage_offset, 2)}V")

        current_rpm = rpm_controller.getTargetSpeed()
        if current_rpm == 256:
            print("Max RPM Reached! Generator is over capacity!")
            max_rpm = True
        else:
            rpm_adjust = round((voltage_offset) / 20, 0)
            if rpm_adjust == 0:
                rpm_adjust = 1
            elif current_rpm + rpm_adjust >= 256:
                rpm_adjust = 1
            print(f"Adjusting RPM from {current_rpm} RPM to {current_rpm + rpm_adjust} RPM")
            rpm_controller.setTargetSpeed(current_rpm + rpm_adjust)
            new_rpm = int(current_rpm + rpm_adjust)
    else:
        volt_stability = 1

    gen_data.update({'l1_volt': l1_voltage, 'l2_volt': l2_voltage, 'volt_stability': volt_stability, 'rpm': new_rpm})
    other_gauges = [['l1_amp', 1], ['l2_amp', 2], ['remaining_su', 3]]

    for item in other_gauges:
        data = remaining_gauges.getLine(item[1])
        if not data.isspace():
            if item[1] == 3:
                data = int(str.split(data, 'su')[0].replace(',', ''))
            else:
            	data = float(str.split(data, " ")[1])
            gen_data.update({item[0]: data})

    try:
        response = requests.post(f"http://{url}", json=gen_data, timeout=2)
    except requests.exceptions.ConnectionError as error:
        print("Connection Refused. Is the cloud server offline?")
    except requests.exceptions.ReadTimeout as error:
        print("Connection Timeout. Is the cloud server offline?")

while shutdown == False:
    check_voltage()
    time.sleep(1)
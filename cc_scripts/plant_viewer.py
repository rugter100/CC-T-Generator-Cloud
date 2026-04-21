import time
import requests

from cc import peripheral
#from cc import os

display = peripheral.wrap("right")
url = '10.1.10.62:2061/getdata'
display.clear()
display.setTextScale(0.5)
display.setCursorPos(1, 1)
display.write("Gen| L1 V/A      | L2 V/A      | RPM | PWR |")

gen_id_list = ['Loc', '1', '2']
loading_icon = "\\-/|"
loading_number = 0

on = True



def update_display():
    try:
        response = requests.post(f"http://{url}", json={'data_request': 'all'}, timeout=2)
        data = response.json()

        display_line = 2

        for generator_key in data['generator_order']:
            generator = data['generators'][generator_key]
            if 'generator_id' in generator.keys():
                bg_color = "ffff"
                if generator['l1_volt'] >= 825 or generator['l1_amp'] >= 2:
                    bg_color += "eeeeeeeeeeeeef"
                elif generator['l1_volt'] >= 800:
                    bg_color += "dddddddddddddf"
                else:
                    bg_color += "7777777777777f"

                if generator['l2_volt'] >= 825 or generator['l2_amp'] >= 2:
                    bg_color += "eeeeeeeeeeeeef"
                elif generator['l2_volt'] >= 800:
                    bg_color += "dddddddddddddf"
                else:
                    bg_color += "7777777777777f"

                if generator['rpm'] >= 250:
                    bg_color += "eeeeef"
                elif generator['rpm'] >= 240:
                    bg_color += "11111f"
                else:
                    bg_color += "dddddf"

                if generator['startup']:
                    power_state = 'On '
                    bg_color += "dddddf"
                    gen_rpm = generator['rpm']
                else:
                    power_state = 'Off'
                    bg_color += "eeeeef"
                    gen_rpm = 0

                text = "{:<3}| {:>5}V {:>3}A | {:>5}V {:>3}A | {:>3} | {} |".format(
                    generator['generator_id'],
                    round(generator['l1_volt'], 2),
                    generator['l1_amp'],
                    round(generator['l2_volt'], 2),
                    generator['l2_amp'],
                    gen_rpm,
                    power_state
                )
            else:
                global loading_number
                text = f"{generator_key:<3}| Controller offline... Waiting for response    {loading_icon[loading_number]}"
                loading_number += 1
                if loading_number == 4:
                    loading_number = 0
                bg_color = "1" * len(text)
            fg_color = "0" * len(text)
            display.setCursorPos(1, display_line)
            display.blit(text, fg_color, bg_color)
            display_line += 1

    except requests.exceptions.ConnectionError as error:
        print("Connection Refused. Is the cloud server offline?")
    except requests.exceptions.ReadTimeout as error:
        print("Connection Timeout. Is the cloud server offline?")

while on:
    update_display()
    time.sleep(2)
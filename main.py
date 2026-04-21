# ver 0.0.1
# Python3.12

import yaml
import libraries.logger as logger

from flask import Flask, request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

log = logger.file_logger()
log.initialize('Main')
log.info("Logging Initialized!")

app = Flask(__name__)

scheduler = BackgroundScheduler(daemon=True)

with open(r'config.yml') as config:
    cfg = yaml.load(config, Loader=yaml.FullLoader)

plant_data = {}

def build_plant_data():
    global plant_data
    plant_data = {'generator_order': [], 'generators': {}}
    for generator_key in cfg['generators']:
        plant_data['generator_order'].append(generator_key)
        plant_data['generators'][generator_key] = {'local': cfg['generators'][generator_key]['local'],'l1_volt': 0, 'l2_volt': 0, 'l1_amp': 0, 'l2_amp': 0, 'rpm': 0, 'startup': False}


build_plant_data()

# Turns on 1 generator
for generator_key in plant_data['generators']:
    if plant_data['generators'][generator_key]['local']:
        plant_data['generators'][generator_key]['startup'] = True
    if not plant_data['generators'][generator_key]['local'] and not plant_data['generators'][generator_key]['startup']:
        plant_data['generators'][generator_key]['startup'] = True
        break


@app.route('/submitdata', methods=['POST'])
def submitdata():
    global plant_data
    post_data = request.get_json()
    gen_id = str(post_data['generator_id'])
    plant_data['generators'][gen_id].update(post_data)
    return jsonify(plant_data['generators'][gen_id])

@app.route('/getdata', methods=['POST'])
def getdata():
    post_data = request.get_json()
    if post_data['data_request'] == 'all':
        return jsonify(plant_data)

def check_load():
    log.info("Checking load on the network.")
    generators_on = 0
    generators_maxed = 0
    for generator in plant_data['generators'].items():
        if generator[1]['startup']:
            if not generator[1]['local']:
                generators_on += 1
                if generator[1]['l1_amp'] == 2 and generator[1]['l2_amp'] == 2:
                    generators_maxed += 1
    log.info(f"Generators On: {generators_on} | Generators at 2A Load: {generators_maxed}")
    if generators_maxed == generators_on:
        for generator_key in plant_data['generators']:
            if not plant_data['generators'][generator_key]['startup']:
                plant_data['generators'][generator_key]['startup'] = True
                log.info(f"Turning on generator {generator_key}")
                break





if cfg['devmode']:
    app.run(debug=True, use_reloader=False, host=cfg['webserver']['bind_address'], port=cfg['webserver']['bind_port'])

elif __name__ == "__main__":

    from waitress import serve

    scheduler.add_job(
        func=check_load,
        trigger=IntervalTrigger(minutes=5),
        id='check_load',
        name='Check Load on generators',
        replace_existing=True
    )
    scheduler.start()

    log.info(f"Starting server on {cfg['webserver']['bind_address']}:{cfg['webserver']['bind_port']}")

    serve(app, host=cfg['webserver']['bind_address'], port=cfg['webserver']['bind_port'], threads=8)
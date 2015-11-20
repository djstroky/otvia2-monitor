from datetime import datetime
import csv
import os

import requests

from monitor import DATA_DIR
from monitor.config import get_config


def flattenjson(b, delim):
    val = {}
    for i in b.keys():
        if isinstance(b[i], dict):
            if i == 'PredictionTimes':
                val[i] = delim.join([j + delim + str(b[i][j]) for j in b[i].keys()])
            else:
                get = flattenjson(b[i], delim)
                for j in get.keys():
                    val[i + delim + j] = get[j]
        elif isinstance(b[i], list):
            for j in range(len(b[i])):
                val[i + '[' + str(j) + ']'] = b[i][j]
        else:
            val[i] = b[i]

    return val


def make_dt():
    return datetime.strftime(datetime.now(), '%Y-%m-%d-%H-%M-%S')


def collect():
    
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    conf = get_config()

    res = requests.get(conf.get('host') + '/art/packet/json/shelter')
    json = res.json()
    
    csvfile = open(os.path.join(DATA_DIR, 'art_log_shelter' + make_dt()), 'wb')
    
    fieldnames = []
    
    # get field names
    for shelter in json['ShelterArray']:
        for item in flattenjson(shelter['Shelter'], '__').keys():
            if item not in fieldnames:
                fieldnames.append(item)
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for shelter in json['ShelterArray']:
        writer.writerow(flattenjson(shelter['Shelter'], '__'))
        
    res = requests.get(conf.get('host') + '/art/packet/json/vehicle')
    json = res.json()
    
    csvfile = open(os.path.join(DATA_DIR, 'art_log_vehicle' + make_dt()), 'wb')
    
    fieldnames = []
    
    # get field names
    for vehicle in json['VehicleArray']:
        for item in flattenjson(vehicle['vehicle'], '__').keys():
            if item not in fieldnames:
                fieldnames.append(item)
    
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    
    for vehicle in json['VehicleArray']:
        writer.writerow(flattenjson(vehicle['vehicle'], '__'))

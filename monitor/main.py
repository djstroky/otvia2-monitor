from collections import Counter
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


def format_dt(dt=datetime.now(), fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.strftime(dt, fmt)


def get_writer(base, fields):
    dt = format_dt(fmt='%Y-%m-%d')
    filename = os.path.join(DATA_DIR, base + '_' + dt + '.csv')
    
    if not os.path.exists(filename):
        writer = csv.DictWriter(open(filename, 'wb'), fieldnames=fields)
        writer.writeheader()
    else:
        writer = csv.DictWriter(open(filename, 'ab'), fieldnames=fields)
        
    return writer


def parse_vehicle(json):
    '''Parses vehicle json response
    
    Returns:
        dict: summary stats about all vehicles
    '''
    
    writer = get_writer('vehicle', 
                        ['Timestamp',
                         'Vehicle ID',
                         'Route ID',
                         'Pattern ID',
                         'Work Piece ID',
                         'Providing Updates',
                         'Location Timestamp',
                         'Location Latitude',
                         'Location Longitude'])
    
    summary = Counter()
    
    for vehicle in json['VehicleArray']:
        summary['Number of Vehicles'] += 1
        vehicle = vehicle['vehicle']
        vout = dict(Timestamp=format_dt())
        vout['Vehicle ID'] = vehicle['id']
        vout['Route ID'] = vehicle['routeID']
        if vehicle['routeID'] != 0:
            summary['Number of Vehicles with a Route ID Assigned'] += 1
        vout['Pattern ID'] = vehicle['patternID']
        vout['Work Piece ID'] = vehicle['workPieceID']
        vout['Providing Updates'] = vehicle['update'] 
        if 'CVLocation' in vehicle:
            summary['Number of Vehicles with Location Data'] += 1
            with vehicle['CVLocation'] as location:
                stamp = format_dt(datetime.fromtimestamp(location['locTime']))
                vout['Location Timestamp'] = stamp
                vout['Location Latitude'] = location['latitude'] / 100000
                vout['Location Longitude'] = location['longitude'] / 100000

        writer.writerow(vout)
        
    return summary


def collect_for_type(url, parser):
    '''Fetch data a given url and feed to parser.
    
    Returns
        Counter: result of parser
    '''
    
    conf = get_config()
    
    res = requests.get(conf.get('host') + url)
    return parser(res.json())


def collect():
    '''Main function to collect all data for the current time.
    '''
    
    '''stops = collect_for_type('/art/packet/json/shelter',
                             parse_stop)'''
    
    vehicle_summary = collect_for_type('/art/packet/json/vehicle', parse_vehicle)

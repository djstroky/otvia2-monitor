from collections import Counter
from datetime import datetime
import csv
import os
import zipfile

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


def do_rollover(base):
    ''' Rollover files.
    Delete anything over 45 days.
    Zip anything not zipped over 7 days.'''
    
    for f in os.listdir(DATA_DIR):
        if f.find(base) > -1:
            f1, ext = os.path.splitext(f)
            dt_diff = datetime.now() - datetime.strptime(f1.replace(base + '_', ''), '%Y-%m-%d')
            if dt_diff.days > 45:
                os.remove(os.path.join(DATA_DIR, f))
            elif dt_diff.days > 7 and ext == '.csv':
                zf = zipfile.ZipFile(os.path.join(DATA_DIR, "%s.zip" % (f1)), "w", zipfile.ZIP_DEFLATED)
                zf.write(os.path.join(DATA_DIR, f), f)
                zf.close()
                os.remove(os.path.join(DATA_DIR, f))       


def get_writer(base, fields):
    dt = format_dt(fmt='%Y-%m-%d')
    filename = os.path.join(DATA_DIR, base + '_' + dt + '.csv')
    
    if not os.path.exists(filename):
        do_rollover(base)
        writer = csv.DictWriter(open(filename, 'wb'), fieldnames=fields)
        writer.writeheader()
    else:
        writer = csv.DictWriter(open(filename, 'ab'), fieldnames=fields)
        
    return writer


def parse_stop(json):
    '''Parses stop json response
    
    Returns:
        dict: summary stats about all stops
    '''
    
    writer = get_writer('stop', 
                        ['Timestamp',
                         'Stop ID',
                         'Stop Name',
                         'Number of Routes',
                         'Number of Predictions',
                         'Routes with Predictions'])
    
    summary = Counter()
    
    for stop in json['ShelterArray']:
        stop = stop['Shelter']
        
        summary['Number of Routes'] += len(stop['routeLogNumbers'])
        
        sout = dict(Timestamp=format_dt())
        sout['Stop ID'] = stop['ShelterId']
        sout['Stop Name'] = stop['ShelterName']
        sout['Number of Routes'] = len(stop['routeLogNumbers'])
        num_predictions = 0
        prediction_routes = ''
        pre = 'shelterPred' + str(stop['ShelterId'])
        for k in stop['PredictionTimes']:
            num_predictions += 1
            prediction_routes += '%s ' % k.split('-')[0].replace(pre, '')
            summary['Routes with Predictions'] += 1
            
        sout['Number of Predictions'] = num_predictions
        sout['Routes with Predictions'] = prediction_routes
        
        writer.writerow(sout)
        
    return summary


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
            print vehicle
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
    
    try:
        os.mkdir(DATA_DIR)
    except:
        pass
    
    stop_summary = collect_for_type('/art/packet/json/shelter',
                                    parse_stop)
    
    vehicle_summary = collect_for_type('/art/packet/json/vehicle', parse_vehicle)
    
    sum_fields = ['Timestamp',
                  'Number of Vehicles',
                  'Number of Vehicles with a Route ID Assigned',
                  'Number of Vehicles with Location Data',
                  'Number of Routes',
                  'Routes with Predictions']
    
    writer = get_writer('summary', sum_fields)
    
    sum_row = dict(Timestamp=format_dt())
    
    for k in stop_summary:
        sum_row[k] = stop_summary[k]
        
    for k in vehicle_summary:
        sum_row[k] = vehicle_summary[k]
        
    for k in sum_fields:
        if k not in sum_row:
            sum_row[k] = '0'
        
    writer.writerow(sum_row)

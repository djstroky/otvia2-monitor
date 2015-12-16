from collections import Counter
from datetime import datetime
import csv
import os
import zipfile

from bs4 import BeautifulSoup
import requests
from requests.exceptions import ConnectionError

from monitor import DATA_DIR
from monitor.config import get_config


class CSVWriter2:

    def __init__(self, base, fields):

        self.base = base
        self.fields = fields

        dt = format_dt(fmt='%Y-%m-%d')

        # prepare archive file for writing
        archive_filename = os.path.join(DATA_DIR, base + '_' + dt + '.csv')

        if not os.path.exists(archive_filename):
            self.do_rollover()
            self.archive_writer = csv.DictWriter(open(archive_filename, 'wb'), fieldnames=fields)
            self.archive_writer.writeheader()
        else:
            self.archive_writer = csv.DictWriter(open(archive_filename, 'ab'), fieldnames=fields)

        # prepare last 2 hours file for writing
        recent_filename = os.path.join(DATA_DIR, base + '_last_2_hours.csv')

        if not os.path.exists(recent_filename):
            self.recent_writer = csv.DictWriter(open(recent_filename, 'wb'), fieldnames=fields)
            self.recent_writer.writeheader()
        else:
            # file exists, copy data less than 2 hours old to temp file
            temp_out_filename = os.path.join(DATA_DIR, base + '_temp.csv')

            with open(recent_filename) as recent, open(temp_out_filename, 'wb') as temp:
                rdr = csv.reader(recent)
                temp_wrtr = csv.writer(temp)

                first_row = True
                for row in rdr:
                    if first_row:
                        temp_wrtr.writerow(row)
                        first_row = False
                        continue

                    dt = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S')
                    if (datetime.now() - dt).seconds < 7200:
                        temp_wrtr.writerow(row)

            os.remove(recent_filename)
            os.rename(temp_out_filename, recent_filename)

            # done copying, open in append mode
            self.recent_writer = csv.DictWriter(open(recent_filename, 'ab'), fieldnames=fields)

    def writerow(self, row):
        self.archive_writer.writerow(row)
        self.recent_writer.writerow(row)

    def do_rollover(self):
        ''' Rollover files.
        Delete anything over 45 days.
        Zip anything not zipped over 7 days.'''

        for f in os.listdir(DATA_DIR):
            if f.find(self.base) > -1 and f.find('last_2_hours') == -1:
                f1, ext = os.path.splitext(f)
                dt_diff = datetime.now() - datetime.strptime(f1.replace(self.base + '_', ''), '%Y-%m-%d')
                if dt_diff.days > 45:
                    os.remove(os.path.join(DATA_DIR, f))
                elif dt_diff.days > 7 and ext == '.csv':
                    zf = zipfile.ZipFile(os.path.join(DATA_DIR, "%s.zip" % (f1)), "w", zipfile.ZIP_DEFLATED)
                    zf.write(os.path.join(DATA_DIR, f), f)
                    zf.close()
                    os.remove(os.path.join(DATA_DIR, f))


def format_dt(dt=datetime.now(), fmt='%Y-%m-%d %H:%M:%S'):
    return datetime.strftime(dt, fmt)


def parse_stop_html(html):
    '''Parses stop html and outputs it without lengthy markup
    '''

    out = ''

    soup = BeautifulSoup(html, 'html.parser')
    out += soup.find_all(class_='labelShelterHeaderStopRow')[0].text.strip()
    out += '<br />'

    rs_listing = soup.find_all(class_='labelShelterRouteListing')[0]

    for rs in rs_listing.find_all('div'):
        rs_text = rs.text.strip()
        if len(rs_text) > 0:
            out += rs_text + '<br />'

    return unicode(out).encode('utf-8')


def parse_stop(json):
    '''Parses stop json response
    
    Returns:
        dict: summary stats about all stops
    '''

    fields = ['Timestamp',
              'Stop ID',
              'Stop Name',
              'Number of Routes',
              'Number of Predictions',
              'Number of Routes with Predictions',
              'Routes with Predictions',
              'Display Text']
    
    writer = CSVWriter2('stop', fields)
    
    summary = Counter()

    if not json or 'ShelterArray' not in json:
        writer.writerow(['No Data' for _ in range(len(fields))])
        return summary
    
    for stop in json['ShelterArray']:
        stop = stop['Shelter']
        
        summary['Number of Route-Stop Pairs'] += len(stop['routeLogNumbers'])
        
        sout = dict(Timestamp=format_dt())
        sout['Stop ID'] = stop['ShelterId']
        sout['Stop Name'] = stop['ShelterName']
        sout['Number of Routes'] = len(stop['routeLogNumbers'])
        sout['Display Text'] = parse_stop_html(stop['WebLabel'])
        num_predictions = 0
        routes_with_predictions = set()
        pre = 'shelterPred' + str(stop['ShelterId'])
        for k in stop['PredictionTimes']:
            num_predictions += 1
            routes_with_predictions.add(k.split('-')[0].replace(pre, ''))
            
        sout['Number of Predictions'] = num_predictions
        sout['Routes with Predictions'] = ' '.join(list(routes_with_predictions))
        sout['Number of Routes with Predictions'] = len(routes_with_predictions)
        summary['Number of Route-Stop Pairs with Predictions'] += len(routes_with_predictions)
        
        writer.writerow(sout)
        
    return summary


def parse_vehicle(json):
    '''Parses vehicle json response
    
    Returns:
        dict: summary stats about all vehicles
    '''

    fields = ['Timestamp',
              'Vehicle ID',
              'Route ID',
              'Pattern ID',
              'Work Piece ID',
              'Providing Updates',
              'Location Timestamp',
              'Location Latitude',
              'Location Longitude']
    
    writer = CSVWriter2('vehicle', fields)
    
    summary = Counter()

    if not json or 'VehicleArray' not in json:
        writer.writerow(['No Data' for _ in range(len(fields))])
        return summary
    
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
            #print vehicle
            summary['Number of Vehicles with Location Data'] += 1
            location = vehicle['CVLocation']
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
    
    try:
        res = requests.get(conf.get('host') + url)
        out = res.json()
    except ConnectionError:
        out = None

    return parser(out)


def collect():
    '''Main function to collect all data for the current time.
    '''
    
    try:
        os.mkdir(DATA_DIR)
    except:
        pass
    
    stop_summary = collect_for_type('/art/packet/json/shelter', parse_stop)
    
    vehicle_summary = collect_for_type('/art/packet/json/vehicle', parse_vehicle)
    
    sum_fields = ['Timestamp',
                  'Number of Vehicles',
                  'Number of Vehicles with a Route ID Assigned',
                  'Number of Vehicles with Location Data',
                  'Number of Route-Stop Pairs',
                  'Number of Route-Stop Pairs with Predictions']
    
    writer = CSVWriter2('summary', sum_fields)
    
    sum_row = dict(Timestamp=format_dt())
    
    for k in stop_summary:
        sum_row[k] = stop_summary[k]
        
    for k in vehicle_summary:
        sum_row[k] = vehicle_summary[k]
        
    for k in sum_fields:
        if k not in sum_row:
            sum_row[k] = '0'
        
    writer.writerow(sum_row)

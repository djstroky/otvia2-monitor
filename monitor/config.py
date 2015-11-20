import ConfigParser
import os

try: 
    input = raw_input
except NameError: 
    pass

from monitor import CONFIG_DIR


class DefaultConfig:
    
    def __init__(self, config_parser):
        self.config_parser = config_parser
        
    def get(self, key):
        return self.config_parser.get('DEFAULT', key)
        

def get_config():
    '''Master function for getting a config file
    
    Returns:
        DefaultConfig: A DefaultConfig instances
    '''
    
    config_filename = os.path.join(CONFIG_DIR, 'monitor.ini')
    if not os.path.exists(config_filename):
        raise Exception('config file config/monitor.ini not found')
        
    config = ConfigParser.ConfigParser()
    config.read(config_filename)
    return DefaultConfig(config)

import os

__import__('pkg_resources').declare_namespace(__name__)


BASE_DIR = os.path.split(os.path.dirname(__file__))[0]
TEMPLATE_DIR = os.path.join(BASE_DIR, 'config_templates')
CONFIG_DIR = os.path.join(BASE_DIR, 'config')
DATA_DIR = os.path.join(BASE_DIR, 'data')

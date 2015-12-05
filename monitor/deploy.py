from deploy_utils.config import ConfigHelper
from deploy_utils.ec2 import launch_new_ec2
from deploy_utils.fab import AmazonLinuxFab

from monitor import CONFIG_DIR, TEMPLATE_DIR


def deploy():
    
    # create config helper
    ConfHelper = ConfigHelper(CONFIG_DIR, TEMPLATE_DIR) 
        
    # launch ec2
    ec2_conf = ConfHelper.get_config('aws')
    ec2_instance, ec2_connection = launch_new_ec2(ec2_conf, True)
    
    # do fab stuff to ec2 instance
    amzn_linux_fab = AmazonLinuxFab(ec2_conf, ec2_instance.public_dns_name)
    amzn_linux_fab.set_timezone('/usr/share/zoneinfo/America/Los_Angeles')
    amzn_linux_fab.update_system()
    amzn_linux_fab.install_custom_monitoring()
    amzn_linux_fab.install_git()

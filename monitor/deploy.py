from deploy_utils.config import ConfigHelper
from deploy_utils.ec2 import launch_new_ec2, tear_down
from deploy_utils.fab import AmazonLinuxFab, unix_path_join
from fabric.api import run, sudo, cd, put
from fabric.context_managers import prefix

from monitor import CONFIG_DIR, TEMPLATE_DIR


# create config helper
ConfHelper = ConfigHelper(CONFIG_DIR, TEMPLATE_DIR) 
    

class OTVia2Fab(AmazonLinuxFab):
    
    def venv(self, cmd, use_sudo=False):
        pre_path = unix_path_join(self.user_home, 'otvia2-monitor', 'bin', 'activate')
        with prefix('source {0}'.format(pre_path)):
            if use_sudo:
                sudo(cmd)
            else:
                run(cmd)
    
    def install_monitor(self):
        run('git clone https://github.com/evansiroky/otvia2-monitor.git')
        run('virtualenv -p /usr/bin/python otvia2-monitor')
        # install gcc so pycrypto can compile
        sudo('yum -y install gcc')
        
        monitor_conf = ConfHelper.get_config('monitor')
        with cd('otvia2-monitor'):
            
            # upload monitoring config
            run('mkdir config')
            put(ConfHelper.write_template(dict(host=monitor_conf.get('host')), 
                                          'monitor.ini'),
                'config')
            
            # install run scripts
            self.venv('python setup.py develop')
            
        # test run of monitor
        run(unix_path_join(self.user_home, 'otvia2-monitor', 'bin', 'monitor'))
        

def deploy():
    
    tear_down_on_error = False
        
    # launch ec2
    ec2_conf = ConfHelper.get_config('aws')
    ec2_instance, ec2_connection = launch_new_ec2(ec2_conf, True)
    
    try:
        # do fab stuff to ec2 instance
        fab = OTVia2Fab(ec2_conf, ec2_instance.public_dns_name)
        fab.set_timezone('/usr/share/zoneinfo/America/Los_Angeles')
        fab.update_system()
        fab.install_custom_monitoring()
        fab.install_git()
        fab.install_monitor()
    except:
        if tear_down_on_error:
            # Terminate EC2 instance.
            tear_down(ec2_instance.id, ec2_connection)

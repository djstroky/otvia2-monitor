import os

from deploy_utils.config import ConfigHelper
from deploy_utils.ec2 import launch_new_ec2, tear_down
from deploy_utils.fab import AmazonLinuxFab, unix_path_join
from fab_deploy.crontab import crontab_update
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
            
            # install node.js server
            server_cfg = dict(server_admin_username=monitor_conf.get('server_admin_username'),
                              server_admin_password=monitor_conf.get('server_admin_password'),
                              server_access_username=monitor_conf.get('server_access_username'),
                              server_access_password=monitor_conf.get('server_access_password'))

            put(ConfHelper.write_template(server_cfg, 'server.js'),
                'config')

            put(ConfHelper.write_template(dict(google_analytics_tracking_id=\
                                               monitor_conf.get('google_analytics_tracking_id')),
                                          'web.js'),
                'config')

            run('npm install')
            run('npm run build')
            
            # redirect port 80 to 3000 for node app
            sudo('iptables -t nat -I PREROUTING -p tcp --dport 80 -j REDIRECT --to-port 3000')
            sudo('service iptables save')
            
            # start server
            run('forever start -a --uid "otvia2-monitor" server/index.js')
            
        # install cron to run monitor script
        with open(os.path.join(TEMPLATE_DIR, 'monitor_crontab')) as f:
            cron_template = f.read()
            
        collect_script = unix_path_join(self.user_home, 'otvia2-monitor', 'bin', 'monitor')
        cron_settings = dict(cron_email=monitor_conf.get('cron_email'),
                             path_to_monitor_script=collect_script)
        cron = cron_template.format(**cron_settings)
        crontab_update(cron, 'otvia2_data_collection')
        

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
        fab.install_node()
        fab.install_monitor()
    except:
        if tear_down_on_error:
            # Terminate EC2 instance.
            tear_down(ec2_instance.id, ec2_connection)

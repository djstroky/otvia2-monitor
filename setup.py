from setuptools import setup, find_packages
 
setup(
    name='monitor',
    packages=find_packages(),
    install_requires=[
        'beautifulsoup4>=4.4.1',
        'deploy_utils>=0.2.0',
        'django-fab-deploy>=0.7.5',
        'requests>=2.5.3'
    ],
    entry_points={
        'console_scripts': [
            'monitor=monitor.main:collect',
            'deploy=monitor.deploy:deploy'
        ]
    }
)

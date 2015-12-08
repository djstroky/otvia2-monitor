from setuptools import setup, find_packages
 
setup(
    name='monitor',
    packages=find_packages(),
    install_requires=[
        'requests>=2.5.3',
        'deploy_utils>=0.2.0'
    ],
    entry_points={
        'console_scripts': [
            'monitor=monitor.main:collect',
            'deploy=monitor.deploy:deploy'
        ]
    }
)

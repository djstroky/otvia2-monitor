from setuptools import setup, find_packages
 
setup(
    name='monitor',
    packages=find_packages(),
    install_requires=[
        'requests>=2.5.3'
    ],
    entry_points={
        'console_scripts': [
            'monitor=monitor.main:collect'
        ]
    }
)

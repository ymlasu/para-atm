from setuptools import setup, find_packages
from os import path

setup(
        name='para-atm',
        version='0.1',
        description='Probabilistic toolset for air traffic safety analysis',
        packages=find_packages(),
        install_requires=[
            'pandas',
            'pyclipper',
            'rdflib',
            'psycopg2-binary',
            'sqlalchemy',
            'bokeh',
            'jpype1==0.6.3'],
        entry_points={
            'console_scripts': [
                'para_atm=PARA_ATM.para_atm:main',
            ],
        },
    )

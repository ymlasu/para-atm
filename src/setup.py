from setuptools import setup, find_packages
from os import path

setup(
        name='PARAATM',
        version='1.0',
        description='Probabilistic toolset for air traffic safety analysis',
        url='https://github.com/mh-swri/NASA_ULI_InfoFusion',
        author='Southwest Research Institute',
        classifiers=[
            'Development Status :: 3 - Alpha',
            'Intended Audience :: ATM researchers',
            'Topic :: NAS Safety',
            'License :: Open',
            ],
        #package_dir={'': 'src/PARA_ATM'},
        packages=find_packages(),
        install_requires=[
            'pandas',
            'pyclipper',
            'rdflib',
            'psycopg2-binary',
            'sqlalchemy',
            'bokeh'],
        entry_points={
            'console_scripts': [
                'para_atm=PARA_ATM.para_atm:main',
            ],
        },
    )

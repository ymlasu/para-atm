#!/home/anaconda3 python
# -*- coding: utf-8 -*-

"""The test function for the weather data parser"""

import os
from paraatm.io.weather_cube_ET import WeatherCubeGenerator

# set parameters to the function in a dictionary
cfg = {'cube_size': 20, 'resize_ratio': 1, 'downsample_ratio': 1}

# Get the current directory
THIS_DIR = os.path.dirname(os.path.abspath(__file__))

# Directory to weather data path
cfg['weather_path'] = os.path.join(THIS_DIR, '..', 'sample_data/weather_parser/echotop_data/')
cfg['trajectory_path'] = os.path.join(THIS_DIR, '..', 'sample_data/weather_parser/Weather_demo_track.csv')

# run the parser on the sample dataset
fun = WeatherCubeGenerator(cfg)
fun.get_cube(save_area=False, save_point=False)

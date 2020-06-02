#!/home/anaconda3 python
# -*- coding: utf-8 -*-

"""The test function for the weather data parser"""

import os
from paraatm.io.weather_cube_ET import weather_cube_generator

# set parameters to the function in a dictionary
cfg = {'cube_size': 20, 'resize_ratio': 1, 'downsample_ratio': 1}

# Get the current directory
cwd = os.path.dirname(os.getcwd())

# Directory to weather data path
cfg['weather_path'] = os.path.join(cwd, 'sample_data/weather_parser/echotop_data/')
cfg['trajectory_path'] = os.path.join(cwd, 'sample_data/weather_parser/Weather_demo_track.csv')

# run the parser on the sample dataset
fun = weather_cube_generator(cfg)
fun.get_cube(save_area=False, save_point=False)
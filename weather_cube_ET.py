#!/home/anaconda3 python
# -*- coding: utf-8 -*-
"""
NASA NextGen NAS ULI Information Fusion

@organization: Arizona State University
@author: Yutian Pang
@date: 2019-02-19
@last updated: 2020-06-01

This script is used to read and process the EchoTop (ET) convective weather products from
the Corridor Integrated Weather System (CIWS). The data can be downloaded from NASA
Sherlock Data Warehouse. url: https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20180004248.pdf

The script takes raw ET convective weather files and the trajectory file as inputs. The outputs are
the processed weather feature cube around each of the coordinates in trajectory file, as well as the
value of the ET right at each coordinate.

"""

import os
import time
import math
import datetime
import numpy as np
import pandas as pd
from netCDF4 import Dataset


class weather_cube_generator(object):
    """
        Read CIWS EchoTop file and return weather values at and around the coordinates based on the trajectory file
        The input to this class should be a dictionary.

        The header of the trajectory file should contain:

        1. UNIX TIME
        2. LATITUDE
        3. LONGITUDE

        The raw EchoTop file should be multiple .nc files updated every 150 seconds

        Sample data can be found under './sample_data/weather_parser' directory

        Parameters
        ----------
        cube_size : int
            size of the weather tensor to take around the current location. If set 20, the return of weather_area
            will have dimension of len(trajectory)-1 x 20 x 20 x 1. And the return of weather_point will have
            dimension of len(trajectory)-1 x [index_x, index_y, value].
        resize_ratio : int
            The ratio to resize the raw ET weather grid. The original resolution is 3520 x 5120. Increase this
            value will make the grid coarser, but increase the area covered around the current location. If set
            10, the raw ET weather map will first resize to resolution 352 x 512, then take a 20 x 20 grid area.
        downsample_ratio : int
            The ratio to equally downsample the trajectory file to reduce the length of the trajectory and reduce
            time to process the data. If the original length of the whole trajectory is 500, set downsample_ratio=10
            means the script will first equally sample 50 points in the whole trajectory ,then process the weather
            data based on the sampled-trajectory.
        weather_path: str
            The path to the weather data.
        trajectory_path: str
            The path to the trajectory data.
    """

    def __init__(self, cfg):
        self.cube_size = cfg['cube_size']
        self.resize_ratio = cfg['resize_ratio']
        self.downsample_ratio = cfg['downsample_ratio']
        self.weather_path = cfg['weather_path']
        self.traj = pd.read_csv(cfg['trajectory_path'])
        self.traj = self.traj.iloc[::self.downsample_ratio, :].reset_index()  # downsample trajectory

    def find_mean(self, x, y, values):
        """Find the mean weather values around the current location

        Parameters
        ----------
        x: int
        The longitude index of the current location in the grid map. after resize.
        y: int
        The latitude index of the current locatuon in the grid map, after resize.
        values: float
        The weather grid array after resize.


        Returns
        -------
        point_t_values: float
        The averaged mean value of EchoTop around the current location.
        """

        # find mean
        x_p_index = self.resize_ratio * np.linspace(x - 1, x + 1, 2 * self.resize_ratio + 1)
        y_p_index = self.resize_ratio * np.linspace(y - 1, y + 1, 2 * self.resize_ratio + 1)

        x_p_index = x_p_index.astype('int')
        y_p_index = y_p_index.astype('int')

        point_t_values = values[y_p_index.min():y_p_index.max(), x_p_index.min():x_p_index.max()]
        point_t_values = np.sum(point_t_values) / (4 * self.resize_ratio ** 2)

        return point_t_values

    def get_cube(self, save_area=False, save_point=False):
        """
        Calculate the weather_tensor and the weather_point around the current location

        Arguments
        ---------
        save_area: Boolean
        If set to True, save the weather_area tensor into a .npy file. Default is False.
        save_point: Boolean
        If set to True, save the weather_point tensor into a .npy file. Default is False.
        """

        y_max, y_min, x_max, x_min = lat2y(53.8742945085336), lat2y(19.35598953632181), lot2x(-61.65138656927017), lot2x(-134.3486134307298)

        dim = np.int32(np.linspace(1, len(self.traj)-1, len(self.traj)-1))
        nn = np.int32(np.linspace(1, self.cube_size, self.cube_size))
        nn2 = np.int32(np.linspace(2, self.cube_size, self.cube_size-1))

        s_y = np.linspace(y_min, y_max, int(3520/self.resize_ratio))
        s_x = np.linspace(x_min, x_max, int(5120/self.resize_ratio))

        step_x = s_x[1] - s_x[0]
        step_y = s_y[1] - s_y[0]

        weather_tensor = []
        point_t = []

        # information need from the original data file
        x = self.traj['LONGITUDE']
        y = self.traj['LATITUDE']
        t = self.traj['UNIX TIME']

        start = time.time()

        for i in dim:

            # compute index
            if (i+1) % int((len(self.traj)/10)) == 0:
                print("Working on Point {}/{}".format(1+i, len(self.traj)))

            # check weather file exists at time i
            weather_file = check_convective_weather_files(self.weather_path, t[i])
            data = Dataset(weather_file)
            values = np.squeeze(data.variables['ECHO_TOP'])

            # search direction
            dx_ = x[i] - x[i-1] + 1e-8
            dire_x = dx_/np.abs(dx_)
            dy_ = y[i] - y[i-1] + 1e-8
            dire_y = dy_ / np.abs(dy_)

            # Line 1  Along the Traj
            slope_m = (lat2y(y[i]) - lat2y(y[i-1]) + 1e-8) / (lot2x(x[i]) - lot2x(x[i-1]) + 1e-8)
            angle_m = math.atan(slope_m)

            # Line 2 Bottom Boundary
            slope_b = -(lot2x(x[i]) - lot2x(x[i-1]) + 1e-8) / (lat2y(y[i]) - lat2y(y[i-1]) + 1e-8)
            angle_b = math.atan(slope_b)

            delta_Xb = np.abs(step_x * self.cube_size * math.cos(angle_b))
            Y_b = lambda s: slope_b * (s - lot2x(x[i])) + lat2y(y[i])
            Xb_2 = lot2x(x[i]) + 0.5 * delta_Xb  # x-coord right-bottom corner
            Yb_2 = Y_b(Xb_2)  # y-coord right-bottom corner

            # point count
            h = 0

            # store 20x20 values
            weather_v = np.zeros((self.cube_size**2, 1))

            # save weather values at traj point
            x_p = np.int(round((lot2x(x[i]) - x_min) / step_x))
            y_p = np.int(round((lat2y(y[i]) - y_min) / step_y))

            point_t_values = self.find_mean(x_p, y_p, values)
            point_t.append((x_p, y_p, point_t_values))

            # Loop to generate all points coordinates
            for i in nn:

                d_x0 = np.abs(step_y * math.cos(angle_m))
                d_y0 = np.abs(step_y * math.sin(angle_m))

                Xb_2i = np.int(round((Xb_2 - x_min) / step_x))
                Yb_2i = np.int(round((Yb_2 - y_min) / step_y))

                point = (Xb_2i, Yb_2i)

                weather_v[h] = self.find_mean(Xb_2i, Yb_2i, values)

                h = h + 1

                for j in nn2:

                    d_x = np.abs(step_x * math.cos(angle_b))

                    Y_b2 = lambda s: slope_b * (s - Xb_2) + Yb_2
                    x_ = Xb_2 - d_x * (j - 1)
                    y_ = Y_b2(x_)

                    x_i = np.int(round((x_ - x_min) / step_x))
                    y_i = np.int(round((y_ - y_min) / step_y))

                    point = (x_i, y_i)  # index of weather

                    weather_v[h] = self.find_mean(x_i, y_i, values)

                    h = h + 1

                Xb_2 = Xb_2 + dire_x * d_x0
                Yb_2 = Yb_2 + dire_y * d_y0

            weather_v = weather_v.reshape(self.cube_size, self.cube_size)
            weather_tensor.append(weather_v)

        print("Total time for one trajectory is: ", time.time() - start)

        # save data
        if save_area is True:
            np.save('weather_area', weather_tensor)
        if save_point is True:
            np.save('weather_point', point_t)


def lat2y(a):
    """
    Calculate the WGS84 latitude into latitude under Mercator Projection

    Parameters
    ----------
    a: Latitude in WGS84.

    Returns
    -------
    Latitude in Mercator
    """
    Radius = 6378137.0  # Radius of Earth
    return math.log(math.tan(math.pi / 4 + math.radians(a) / 2)) * Radius


def lot2x(a):
    """
    Calculate the WGS84 longitude into longitude under Mercator Projection

    Parameters
    ----------
    a: longitude in WGS84.

    Returns
    -------
    longitude in Mercator
    """
    Radius = 6378137.0  # Radius of Earth
    return math.radians(a) * Radius


def find_nearest_value(array, num):
    """
    Find the nearest value to a given a number in a pre-defined array

    Parameters
    ----------
    array: float, int
    The reference array.

    Returns
    -------
    num: float
    The number we are interested.
    """
    nearest_val = array[abs(array - num) == abs(array - num).min()]
    return nearest_val


def check_convective_weather_files(weather_path, unix_time):
    """
    Find the closest ET weather files corresponding to the time of the current location

    Parameters
    ----------
    weather_path: str
    The path to the weather data.
    unix_time: int
    The unix time of the current location

    Returns
    -------
    file_path: str
    The path to the closest ET weather file at the current location and the current time
    """
    pin = datetime.datetime.utcfromtimestamp(int(float(unix_time))).strftime('%Y%m%d %H%M%S')  # time handle to check CIWS database
    array = np.asarray([0, 230, 500, 730,
                        1000, 1230, 1500, 1730,
                        2000, 2230, 2500, 2730,
                        3000, 3230, 3500, 3730,
                        4000, 4230, 4500, 4730,
                        5000, 5230, 5500, 5730])

    nearest_value = int(find_nearest_value(array, 0.001+np.asarray([int(eliminate_zeros(pin[-4:]))])))  # find the closest time for downloading data from CIWS
    nearest_value = make_up_zeros(str(nearest_value))  # make up zeros for 0 230 500 730

    filename = pin[:8] + "ET/ciws.EchoTop." + pin[:8] + "T" + str(pin[-6:-4]) + nearest_value + "Z.nc"

    file_path = weather_path + filename
    return file_path


def eliminate_zeros(num):
    """
    clear the zeros in the output of the unix to time transformation.

    Parameters
    ----------
    num: float
    A four digit number represents the minute and second time.

    Returns
    -------
    num: float
    The cleared last four digits time
    """
    if num[0] == '0' and num[1] == '0' and num[2] == '0':
        return num[3]
    if num[0] == '0' and num[1] == '0' and num[2] != '0':
        return num[2:]
    if num[0] == '0' and num[1] != '0':
        return num[1:]
    if num[0] != '0':
        return num


def make_up_zeros(str):
    """
    makeup the zeros to write the correct name of the weather ET file

    Parameters
    ----------
    str: str
    The objective string of numbers to makeup

    Returns
    -------
    str: str
    The string with four numbers
    """
    if len(str) == 4:
        return str
    if len(str) == 3:
        return "0" + str
    if len(str) == 2:
        return "00" + str
    if len(str) == 1:
        return "000" + str





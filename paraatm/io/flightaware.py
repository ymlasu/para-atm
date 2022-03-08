# -*- coding: utf-8 -*-
"""Functions for extracting trajectory data from flightaware"""

import numpy as np
import pandas as pd
import datetime


def extract_flightaware_data(FA_URL):   

    dfs = pd.read_html(FA_URL)
    traj_mat = dfs[0]
    traj_mat.drop(labels=0,axis=0,inplace=True)

    # format strings
    time_format = '%a %I:%M:%S %p'
    LatLon_format = "^(\\-?\d+\.\d{4}?)" # regex extracts the following: from start opf string (^) with possible -ve (\\-?) unlimited digits in series (\d+) a decimal point (\.) four digits \d{4} 
    Course_TAS_format = "(\\-?\d+)"

    # Time Stamps
    format_time_col(traj_mat, time_format)

    # Latitude
    format_col(traj_mat,'LatitudeLat',LatLon_format)

    # Longitude
    format_col(traj_mat,'LongitudeLon',LatLon_format)
    
    # Course
    format_col(traj_mat,'CourseDir',Course_TAS_format)
    
    # TAS kts
    format_col(traj_mat,'kts',Course_TAS_format)
    
    # TAS mph
    format_col(traj_mat,'mph',Course_TAS_format)
    
    # Altitude ft
    format_alt_col(traj_mat,'feet')
        
    # ROCD
    traj_mat['Rate'] = traj_mat['Rate'].fillna(0)

    # Rename columns
    traj_mat.rename(columns={traj_mat.columns[0]: "Time_s", "LatitudeLat": "Latitude", "LongitudeLon": "Longitude", "CourseDir": "Course_deg", "kts": "TAS_kts", "mph": "TAS_mph", "feet": "Altitude_ft", "Rate": "ROCD"}, inplace = True)

    # Remove NaN entries
    is_NaN = traj_mat.isnull()
    rows_with_NaN = is_NaN.any(axis=1) # Test for at least one NaN in each row
    traj_mat = traj_mat[~rows_with_NaN] 

    return traj_mat


def format_time_col(database, format_string): 

    col_head = database.columns[0] # assumes time is the first entry
    temp_col = database[col_head].str.slice(0,15)   
    temp_col = pd.to_datetime(temp_col,format=format_string,errors='coerce')
    temp_col = temp_col-temp_col[1]
    
    di = {'Mon':0, 'Tue':1, 'Wed':2, 'Thu':3, 'Fri':4, 'Sat':5, 'Sun':6}
    seconds_offset = database[col_head].str.slice(0,3)
    seconds_offset = seconds_offset.replace(di)*24*60*60
    
    database[col_head] = temp_col.dt.total_seconds() + seconds_offset - seconds_offset[1]

    return 


def format_alt_col(database, col_head): 

    # Note: The extries are presented in duplicated & concatinated form, e.g.: 475 is displayed as 475475
    temp_col = database[col_head].replace(np.nan,0) 
    temp_col = pd.to_numeric(temp_col,errors='coerce') 

    temp_len = temp_col.astype(str)
    temp_len = temp_len.str.len()

    database[col_head] = np.floor(temp_col/pow(10,temp_len//2)) 

    return 


def format_col(database, col_head, format_string): 

    database[col_head] = database[col_head].str.extract(format_string) 
    database[col_head] = database[col_head].astype('float')
    
    return 
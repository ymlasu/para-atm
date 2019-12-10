"""Functions for interfacing to NATS input/output files"""

from pathlib import Path
import pandas as pd
import numpy as np


def read_nats_output_file(filename, interp=False):
    """Read the specified NATS output file

    Return corresponding formatted pandas DataFrame"""
    #trajectory record rows have different fields than header rows
    cols = ['time','lat','lon','altitude','rocd','tas','tas_ground','heading','fpa','sect_ind','sect_name','mode','dest_elev','nrows']

    #skip the initial header of the csv file
    output = pd.read_csv(filename, header=None, names=cols, skiprows=9)
    results = pd.DataFrame()

    #cycle through header rows
    for index,row in output[output['nrows'] > 0].iterrows():
        #rows start immediately after header, end after specified nrows
        start = index+1
        end = start+int(row['nrows'])
        #copy acid to unused column of trajectory rec
        output.iloc[start:end,-1] = row['lon']
        #copy origin
        output.iloc[start:end,-2] = row['rocd']
        #copy destination
        output.iloc[start:end,6] = row['tas']
        results=results.append(output.iloc[start:end][['time','nrows','tas_ground','dest_elev','lat','lon','altitude','rocd','tas','heading','sect_name','mode']])

    col = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
    results.columns = col
    results['time'] = pd.to_datetime(results['time'].astype(float),unit='s')
    floats = ['latitude','longitude','altitude','rocd','tas','heading']
    strs = ['callsign','origin','destination','sector','status']
    results[floats] = results[floats].astype(float)
    results[strs] = results[strs].astype(str).fillna('unknown')
    if interp and (results.at[2,'time'] - results.at[1,'time']) >= pd.to_timedelta('1s'):
        temp = pd.DataFrame()
        results = results.set_index('time')
        for acid in np.unique(results['callsign']):
            upsample = results[results['callsign']==acid].resample('ms')
            interp = upsample.interpolate(method='linear')
            try:
                interp[strs] = interp[strs].interpolate(method='pad')
            except Exception as e:
                print(e)
            temp = temp.append(interp,ignore_index=True)
        results = temp.fillna(method='ffill')

    return results

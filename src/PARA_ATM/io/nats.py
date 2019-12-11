"""Functions for interfacing to NATS input/output files"""

import pandas as pd
import numpy as np
import linecache
from io import StringIO


def read_nats_output_file(filename):
    """Read the specified NATS output file

    Parameters
    ----------
    filename : str
        Input file to read

    Returns
    -------
    Single formatted data frame"""

    # Read header information out of specific line numbers
    header_cols = linecache.getline(filename, 5).strip()[3:].split(',')
    data_cols = linecache.getline(filename, 6).strip()[3:].split(',')
    start_time = int(linecache.getline(filename, 8))

    # Read all lines after header
    with open(filename, 'r') as f:
        lines = f.readlines()[9:]

    # Flag header lines, which may occur throughout the file
    is_header_line = [line.split(',')[0].isalpha() for line in lines]
    header_indices = np.where(is_header_line)[0]

    # Read in data by iterating over the header rows.  Each header row
    # specifies the number of records that follow.  That number is
    # used to find the corresponding subset of data lines associated
    # with the header, and those lines are read in as a DataFrame
    # according to the column names defined above.
    df = pd.DataFrame(columns=data_cols + ['callsign','origin','destination'])
    for header_idx in header_indices:
        header_row = pd.read_csv(StringIO(lines[header_idx]), header=None, names=header_cols).iloc[0]
        nrows = header_row['number_of_trajectory_rec']
        aircraft_df = pd.read_csv(StringIO('\n'.join(lines[header_idx+1:header_idx+1+nrows])), header=None, names=data_cols)
        # Fill in auxiliary data that comes from the header row
        aircraft_df['callsign'] = header_row['callsign']
        aircraft_df['origin'] = header_row['origin_airport']
        aircraft_df['destination'] = header_row['destination_airport']
        df = df.append(aircraft_df)


    df.rename(columns={'timestamp(UTC sec)':'time',
                       'course':'heading',
                       'rocd_fps':'rocd',
                       'sector_name':'sector',
                       'tas_knots':'tas',
                       'flight_phase':'status',
                       'altitude_ft':'altitude'},
              inplace=True)
    df['time'] += start_time
    df['time'] = pd.to_datetime(df['time'], unit='s')

    # Keep only selected columns
    selected_cols = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
    df = df[selected_cols]

    return df

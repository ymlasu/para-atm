"""Utility functions for file input/output"""

from enum import Enum, auto
import pandas as pd

from . import nats
from . import iff

class FileTypes(Enum):
    """Enumeration of file types"""
    UNKNOWN = auto()
    NATS = auto()
    IFF = auto()
    CSV = auto()

def detect_data_file_type(filename):
    """Try and detect the format of a given data file

    Returns
    -------
    Instance of FileTypes Enum
    """
    with open(filename,'r') as f:
        line = f.readline()
    if line.startswith('*'):
        return FileTypes.NATS
    elif 'IFF' in line:
        return FileTypes.IFF
    elif ',' in line:
        # Assume that it is a regular CSV file
        return FileTypes.CSV
    else:
        return FileTypes.UNKNOWN

def read_csv_file(filename):
    """Read a CSV file previously created by PARA_ATM"""
    df = pd.read_csv(filename, converters={'time':pd.to_datetime})
    return df

def write_csv_file(df, filename):
    """Write a DataFrame to csv"""
    df.to_csv(filename, index=False)

def read_data_file(filename, *args, **kwargs):
    """Detect file format and read scenario data

    Supports NATS and IFF format

    Parameters
    ----------
    filename : str
    """
    filetype = detect_data_file_type(filename)

    if filetype == FileTypes.NATS:
        return nats.read_nats_output_file(filename, *args, **kwargs)
    elif filetype == FileTypes.IFF:
        return iff.read_iff_file(filename, *args, **kwargs)
    elif filetype == FileTypes.CSV:
        return read_csv_file(filename)
    else:
        raise ValueError('unrecognized file type')

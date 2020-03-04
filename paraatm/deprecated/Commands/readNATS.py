"""

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 02/04/2019

Visualize NATS output CSV file

"""

from pathlib import Path
import pandas as pd
import numpy as np
import os

from paraatm.io.nats import read_nats_output_file

class Command:
    """
        args:
            filename = name of the NATS simulation output csv
    """
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, filename, **kwargs):
        self.kwargs = {}
        if type(filename) == str:
            self.filename = filename
        else:
            self.filename = filename[0]
            for i in filename[1:]:
                k,v = i.split('=')
                self.kwargs[k] = v
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                command name to be passed to MapView, etc.
                results = dataframe of shape (# position records, 12)
        """
        if self.filename == '':
            return ('readNATS',pd.DataFrame())

        parentPath = str(Path(__file__).parent.parent.parent)
        results = read_nats_output_file(os.path.join(parentPath, 'NATS', self.filename))
        print(results)

        return ["readNATS", results]

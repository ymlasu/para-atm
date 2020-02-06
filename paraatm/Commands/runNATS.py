"""

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 05/30/2019

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

"""

import os
import imp
from pathlib import Path

class Command:
    """
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    """
    
    def __init__(self, params):
        """
            params (list): list of str where element 0 is the NATS module name and all other elements are arguments to pass
        """
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.module = params[0]
        self.params = params[1:]

    def executeCommand(self):
        """
            run the NATS script
        """
        #NATS must be run from this directory to find its classes
        os.system('cd ' + self.NATS_DIR)
        #imp is robust to special characters in filename (e.g. *beta_1.5.py, etc.)
        open_file,file_name,description = imp.find_module(self.module, [self.NATS_DIR + '/scriptsSwRI/'])
        module = imp.load_module(self.module+'.py',open_file,file_name,description)
        #we expect a filename for the simulation output
        results = module.main(self.params)

        return ["runNATS",results]

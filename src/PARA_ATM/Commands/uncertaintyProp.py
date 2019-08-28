'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 05/30/2019

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

'''

import PARA_ATM
from PARA_ATM.Commands.Helpers import DataStore
import numpy as np

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self,safety_module):
        self.mod_name = safety_module.split('(')[0]
        self.in_file = safety_module.split('(')[1][:-1]
        self.safety_module = getattr(PARA_ATM.Commands,self.mod_name)
        self.n_samples = 1
        self.uncertainty_sources = ['atc','pilot','vehicle']
        self.states = ['nominal']

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):

        db_access = DataStore.Access()

        dist_objs = [db_access.getCentaurDist(subject,state) for subject in self.uncertainty_sources for state in self.states]


        #Create random variable
        rv_vector = np.array([np.array(dist.sample(self.n_samples)) for dist in dist_objs]).reshape(-1,3)

        #propagate
        results = [self.safety_module.Command([self.in_file,rv]).executeCommand() for rv in rv_vector]
        print(results)
        return ["uncertaintyProp", results]

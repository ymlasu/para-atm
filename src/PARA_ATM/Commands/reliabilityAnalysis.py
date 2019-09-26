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
import centaur
centaur.CentaurUtils.initialize_centaur()

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    def __init__(self,safety_module):
        """
            uncertaintyProp command propagates uncertainty from given sources through a given safety metric
            args:
                safety_module (str) : the module to calculate the safety metric and its parameters
                n_samples (int) : the number of samples required from the distribution(s)
        """
        #parse the safety_module string
        self.mod_name = safety_module.split('(')[0]
        self.in_file = safety_module.split('(')[1][:-1]
        #load the module
        self.safety_module = getattr(PARA_ATM.Commands,self.mod_name)

        #future args for uncertaintyProp
        self.n_samples = 1000
        self.uncertainty_sources = ['atc','pilot','vehicle']
        self.states = ['nominal']
        self.threshold = 0.2

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                results (list) : [moduleName, aggregated return from the safety module
        """

        #instantiate helper function module for db access
        db_access = DataStore.Access()

        #get Centaur distribution objects from the database
        dist_objs = [db_access.getCentaurDist(subject,state) for subject in self.uncertainty_sources for state in self.states]

        #create random variable matrix
        v = centaur.RV_Vector()
        for obj in dist_objs:
            v.append(obj)

        def min_fpf(rts):
            return np.min(self.safety_module.Command([self.in_file,rts]).executeCommand()[1])

        context = centaur.ReliabilityContext(v,min_fpf,-1,self.threshold)
        method=centaur.ReliabilityMethod()
        method.new_LHS(self.n_samples)
        context.reliability_analysis(method)

        prob_of_failure = method.get_pf()
        prop_samples = method.get_output_samples_data(self.n_samples)

        return ["reliabilityAnalysis", [prob_of_failure,prop_samples]]

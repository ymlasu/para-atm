"""

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 05/30/2019

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

"""

import numpy as np

from PARA_ATM.Commands import runNATS,readNATS
import PARA_ATM.Commands
from PARA_ATM import DataStore

import centaur

centaur.CentaurUtils.initialize_centaur()

class Command:
    """
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    """
    
    def __init__(self,safety_module):
        """
            uncertaintyProp command propagates uncertainty from given sources through a given safety metric
            args:
                safety_module (str) : the module to calculate the safety metric and its parameters
                n_samples (int) : the number of samples required from the distribution(s)
        """
        #parse the safety_module string
        if type(safety_module) == list:
            self.mod_name = safety_module[0].split('(')[0]
            self.in_file = safety_module[0].split('(')[1]
            self.args = safety_module[1:]
            self.args[-1]=self.args[-1][:-1]
        else:
            self.mod_name = safety_module.split('(')[0]
            self.in_file = safety_module.split('(')[1][:-1]
        #load the module
        self.safety_module = getattr(PARA_ATM.Commands,self.mod_name)

        #future args for uncertaintyProp
        self.n_samples = 5
        if 'NATS' in self.mod_name:
            self.uncertainty_sources = ['departure_delay']
        else:
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
        if 'NATS' not in self.mod_name:
            dist_objs = [db_access.getCentaurDist(subject,state) for subject in self.uncertainty_sources for state in self.states]
        else:
            mean_lat = 40.995819091796875;
            std_dev_lat = 0.01*mean_lat;
            sample_sz_lat = 5;
            rv = centaur.Distribution()
            x = np.linspace(1,1200,1200)
            probs = (np.exp(-(np.log(x) - 120)**2 / (2 * 30**2))
                     / (x * 120 * np.sqrt(2*np.pi)))
            probs /= np.sum(probs)
            print(probs,np.sum(probs))
            rv.new_discrete(x,probs)
            dist_objs = [rv,]

        #create random variable matrix
        v = centaur.RV_Vector()
        for obj in dist_objs:
            v.append(obj)

        def min_fpf(rts):
            return np.min(self.safety_module.Command([self.in_file,rts]).executeCommand()[1])
        
        def nats_lat(lats):
            data = readNATS.Command(self.safety_module.Command([self.in_file]+self.args+[lats]).executeCommand()[1]).executeCommand()[1]
            mean_lat = 40.995819091796875;
            std_dev_lat = 0.01*mean_lat;
            return np.std(data['latitude'])/std_dev_lat

        def nats_departure(delays):
            data = readNATS.Command(self.safety_module.Command([self.in_file]+self.args+[delays]).executeCommand()[1]).executeCommand()[1]
            print(data)
            print(data[data['status']=='FLIGHT_PHASE_TAKEOFF'].iloc[0,0])
            return data[data['status']=='FLIGHT_PHASE_TAKEOFF'].iloc[0,0]


        nats_departure(1)

        if 'NATS' in self.mod_name:
            context = centaur.ReliabilityContext(v,nats_lat,1,2)
        else:
            context = centaur.ReliabilityContext(v,min_fpf,-1,self.threshold)
        method=centaur.ReliabilityMethod()
        method.new_LHS(self.n_samples)
        context.reliability_analysis(method)

        prob_of_failure = method.get_pf()
        prop_samples = method.get_output_samples_data(self.n_samples)

        print(prob_of_failure)
        print(prop_samples)
        return ["reliabilityAnalysis", [prob_of_failure,prop_samples]]

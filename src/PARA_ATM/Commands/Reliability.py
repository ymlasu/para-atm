'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Command to plot airspeed vs altitude regression curve for a given callsign as argument.

'''

from PARA_ATM import *

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, airportIATA):
        self.cursor = cursor
        self.AirportIATA = airportIATA
        import uli_pyre_gp
        
    #User-defined method datafetch to perform a set of operations. This can be changed as per need.
    def dataFetch(self, flightCallsign):
        dataStoreAccess = DataStore.Access("API_KEY")
        self.flightData = dataStoreAccess.getFlightHistory(flightCallsign)
        self.xParameter = [i[4] for i in self.flightData]
        self.yParameter = [i[5] for i in self.flightData]
        
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        #TODO: Replace what we can with real data
        capacity_probs = [.57, .18, .25]
        capacity_vals = [96, 84, 72]        
        demand_mean = 64.
        demand_stdv = 8.

        #format capacity and demand to initialize analysis
        capacity = (capacity_probs,capacity_vals)
        demand = (demand_mean,demand_stdv)

        reliability = uli_pyre_gp.ReliabilityAnalysis(capacity,demand)
        #pass custom limit state function and
        #analysis type. options:
        #                       'MC' : Monte Carlo
        #                       'EGRA' : EGRA
        results = reliability.analyze(custom_limit_state=None,analysis_type='MC')
        return results

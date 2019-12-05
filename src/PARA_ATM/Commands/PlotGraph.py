'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Command to plot airspeed vs altitude graph for a given callsign as argument.

'''

import matplotlib.pyplot as plt

from PARA_ATM import DataStore

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, flightCallsign):
        self.cursor = cursor
        self.flightCallsign = flightCallsign
        
    #User-defined method datafetch to perform a set of operations. This can be changed as per need.
    def dataFetch(self, flightCallsign):
        dataStoreAccess = DataStore.Access("API_KEY")
        self.flightData = dataStoreAccess.getFlightHistory(flightCallsign)
        self.xParameter = [float(i[4]) for i in self.flightData]
        self.yParameter = [float(i[5]) for i in self.flightData]
        
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        self.dataFetch(self.flightCallsign)
        figure = plt.figure() 
        plt.plot(self.xParameter, self.yParameter) 
        plt.xlabel("Altitude")
        plt.ylabel("Speed")
        plt.title(self.flightCallsign)
        figure.canvas.set_window_title('PARA-ATM Graph Plot') 
        plt.show()

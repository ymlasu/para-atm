'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Example user command to plot all airports in the US.

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
        self.airportIATA = airportIATA
        
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        self.cursor.execute("SELECT * FROM airports WHERE iata = %s", ("" + self.airportIATA,))
        results = self.cursor.fetchall()
        latitude = results[0][1]
        longitude = results[0][2]
        return ["Airport", latitude, longitude]
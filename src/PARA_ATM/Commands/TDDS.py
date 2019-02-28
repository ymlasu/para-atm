'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Example user command to plot all airports in the US.

'''

from PARA_ATM import *
import pandas as pd

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
        self.cursor.execute("SELECT latitude,longitude FROM airports WHERE iata='%s'" %(""+self.airportIATA))
        lat,lon = self.cursor.fetchall()[0]
        lat,lon = float(lat),float(lon)
        self.cursor.execute("SELECT time,callsign,status,lat,lon FROM smes WHERE lat>'%f' AND lat<'%f' AND lon>'%f' AND lon<'%f'" %(lat-1,lat+1,lon-1,lon+1))
        results = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','status','latitude','longitude'])
        #self.cursor.execute("SELECT time,track,lat,lon FROM asdex WHERE airport='%s' AND lat>'%f'" %("K"+self.airportIATA,lat-1))
        #asdex = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','latitude','longitude'])
        return ['TDDS',results,self.airportIATA]

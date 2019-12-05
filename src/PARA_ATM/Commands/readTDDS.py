'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 28/02/2019

Pull ASDE-X and SMES data for visualization at given airport

'''

import pandas as pd

class Command:
    """
        args:
            airportIATA = airport to center on
            db          = which tables to query
    """
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, airportIATA, db=('smes',)):
        self.cursor = cursor
        self.airportIATA = airportIATA
        self.db = db
        
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                Name of command to pass to MapView, etc.
                results = dataframe of shape (# aircraft, 5)
                          columns = time UTC, aircraft id, smes status, lat, lon
                airport = airport passed in as argument
        """
        #get airport location
        self.cursor.execute("SELECT latitude,longitude FROM airports WHERE iata='%s'" %(""+self.airportIATA))
        lat,lon = self.cursor.fetchall()[0]
        lat,lon = float(lat),float(lon)
        
        #use airport location to find flights
        if 'smes' in self.db:
            self.cursor.execute("SELECT time,callsign,status,lat,lon FROM smes WHERE lat>'%f' AND lat<'%f' AND lon>'%f' AND lon<'%f'" %(lat-1,lat+1,lon-1,lon+1))
            results = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','status','latitude','longitude'])
        if 'asdex' in self.db:
            self.cursor.execute("SELECT time,stid,track,lat,lon FROM asdex WHERE airport='%s' AND lat>'%f'" %("K"+self.airportIATA,lat-1))
            asdex = pd.DataFrame(self.cursor.fetchall(),columns=['time','status','callsign','latitude','longitude'])
        #append both db results
        if len(self.db) > 1:
            results = results.append(asdex)
        #only asdex queried
        elif len(self.db) ==1 and 'asdex' in self.db:
            results = asdex

        return ['readTDDS',results,self.airportIATA]

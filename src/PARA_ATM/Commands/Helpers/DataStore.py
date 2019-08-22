import psycopg2
import pandas as pd

class dbError(Exception):
    def __init__(self):
        Exception.__init__(self,'empty query')

class Access:
    
    def __init__(self):
        self.connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
        self.cursor = self.connection.cursor()
        
    def getAirportLocation(self, airportCode):
        self.cursor.execute("SELECT * FROM airports WHERE iata = %s", ("" + airportCode,))
        results = self.cursor.fetchall()
        latitude = results[0][1]
        longitude = results[0][2]
        return latitude, longitude
        
    def getFlightHistory(self, callsign):
        self.cursor.execute("SELECT * FROM flight_data WHERE callsign = %s", ("" + callsign,))
        results = self.cursor.fetchall()
        return results
    
    def getIFFdata(self, filename, kwargs):
        query = "SELECT * FROM \"%s\""%filename
        conditions = []
        for k,v in kwargs.items():
            conditions.append("%s='%s'"%(k,v))
        if kwargs:
            query += " WHERE "
            query += " AND ".join(conditions)
        self.cursor.execute(query)
        if bool(self.cursor.rowcount):
            results = pd.DataFrame(self.cursor.fetchall())
            results.columns = ['id','time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','status']
            del results['id']
            results[['latitude','longitude','altitude','heading']] = results[['latitude','longitude','altitude','heading']].replace(r'[^0-9,.,-]+','0',regex=True)
            results[['latitude','longitude','altitude','heading']] = results[['latitude','longitude','altitude','heading']].astype(float)
            results['status'] = results['status'].fillna('TAKEOFF/LANDING')
            results = results[results['latitude'] != -100]
            return ['readIFF', results, filename]
        else: raise dbError

    def getNATSdata(self, filename, kwargs):
        query = "SELECT * FROM \"%s\""%filename
        conditions = []
        for k,v in kwargs.items():
            conditions.append("%s='%s'"%(k,v))
        if kwargs:
            query += " WHERE "
            query += " AND ".join(conditions)
        self.cursor.execute(query)
        results = pd.DataFrame(self.cursor.fetchall())
        results.columns = ['id','time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
        del results['id']
        del results['sector']
        return ['readNATS',results,filename]

    def getSMESData(self, airport):
        self.cursor.execute("SELECT * FROM smes WHERE airport = %s" %airport)
        results = self.cursor.fetchall()
        return results

    def getReaction(self,subject,state):
        """
        get the distribution of reaction times for a given subject
        args:
            subject (str): one of ['pilot','atc','vehicle']
        returns:
            dist_type (str),
            loc (float),
            scale (float),
            args (list)
        """

        self.cursor.execute("SELECT * FROM %s_uncertainty WHERE state='%s'"%(subject.lower(),state.lower()))
        results = self.cursor.fetchall()[0]
        print(results)
        index,dist_type,params,state = results
        params = params.split(',')
        args = [float(p) for p in params[:-2]]
        scale = float(params[-1])
        loc = float(params[-2])
        return dist_type,loc,scale,args

    def getCentaurDist(self,table,key):
        """
        get the distribution of reaction times for a given subject
        args:
            table (str): table name
            key (str): the primary key of the table
        returns:
            dist_type (str),
            loc (float),
            scale (float),
            args (list)
        """

        self.cursor.execute("SELECT * FROM %s_uncertainty WHERE key='%s'"%(table.lower(),key.lower()))
        results = self.cursor.fetchall()[0]
        print(results)
        index,dist_type,params,key = results
        params = params.split(',')
        args = [float(p) for p in params[:-2]]
        scale = float(params[-1])
        loc = float(params[-2])

        rv=centaur.Distribution()

        distribution = getattr('centaur.Distribution','new_%s'%dist_type)
        return distribution(loc,scale,*args)

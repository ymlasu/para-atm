from PARA_ATM import *

class Access:
    
    def __init__(self, API_key):
        self.API_key = API_key
        self.connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
        self.cursor = self.connection.cursor()
        
    def getAirportLocation(self, airportCode):
        self.cursor.execute("SELECT * FROM airports WHERE iata = %s", ("" + airportCode,))
        results = self.cursor.fetchall()
        latitude = results[0][1]
        longitude = results[0][2]
        return latitude, longitude
        
    def getHumanFactorsData(self, callsign, date):
        self.cursor.execute("SELECT * FROM human_factors WHERE callsign = %s AND date = %s", ("" + callsign,"" + date,))
        results = self.cursor.fetchall()
        return results

    def getAtcData(self, callsign, date):
        self.cursor.execute("SELECT * FROM atc WHERE callsign = %s AND date = %s", ("" + callsign,"" + date,))
        results = self.cursor.fetchall()
        return results
    
    def getFlightParameters(self, callsign, date):
        self.cursor.execute("SELECT * FROM flight_parameters WHERE callsign = %s AND date = %s", ("" + callsign,"" + date,))
        results = self.cursor.fetchall()
        return results
    
    def getSchedule(self, callsign, date):
        self.cursor.execute("SELECT * FROM schedule WHERE callsign = %s AND date = %s", ("" + callsign,"" + date,))
        results = self.cursor.fetchall()
        return results

    def getTrajectory(self, callsign, date):
        self.cursor.execute("SELECT * FROM trajectory WHERE callsign = %s AND date = %s", ("" + callsign,"" + date,))
        results = self.cursor.fetchall()
        return results
    
    def getFlightHistory(self, callsign):
        self.cursor.execute("SELECT * FROM flight_data WHERE callsign = %s", ("" + callsign,))
        results = self.cursor.fetchall()
        return results
    
    def addHumanFactorsData(self, callsign, date, atc_recording_transcript, pilot_recording_transcript, computer_vision_derivation):
        self.cursor.execute("INSERT INTO human_factors (callsign, date, atc_recording_transcript, pilot_recording_transcript, computer_vision_derivation) VALUES ('" + callsign + "', '" + date + "', '" + atc_recording_transcript + "', '" + pilot_recording_transcript + "', '" + computer_vision_derivation + "')")
        self.connection.commit()
        
    def addAtcLogs(self, callsign, date, waypoints, communication_timestamps):
        self.cursor.execute("INSERT INTO atc (callsign, date, waypoints, communication_timestamps) VALUES ('" + callsign + "', '" + date + "', '" + waypoints + "', '" + communication_timestamps + "')")
        self.connection.commit()
        
    def addFlightParameters(self, callsign, date, altitude, squawk, velocity, vertical_speed, heading):
        self.cursor.execute("INSERT INTO flight_parameters(callsign, date, altitude, squawk, velocity, vertical_speed, heading) VALUES ('" + callsign + "', '" + date + "', '" + altitude + "', '" + squawk  + "', '" +  velocity+"', '" +  vertical_speed + "', '" + heading + "')")
        self.connection.commit()
        
    def addFlightSchedule(self, callsign, date, arrival_time, departure_time):
        self.cursor.execute("INSERT INTO schedule(callsign, date, arrival_time, departure_time) VALUES ('" + callsign + "', '" + date + "', '" + arrival_time + "', '" + departure_time + "')")
        self.connection.commit()
        
    def addTrajectoryData(self, callsign, date, timestamp, latitude, longitude):
        self.cursor.execute("INSERT INTO trajectory(callsign, date, timestamp, latitude, longitude) VALUES ('" + callsign + "', '" + date + "', '" + timestamp + "', '" + latitude + "', '" + longitude + "')")
        self.connection.commit()
        
'''      
dataStoreAccess = Access("APIKEY")
#Example Server URL: http://localhost/connect/dataStoreAccess/addAtcLogs
latitude, longitude = dataStoreAccess.getAirportLocation("PHX")
humanFactors = dataStoreAccess.getHumanFactorsData("AAL429", "12111111")
atcLogs = dataStoreAccess.getAtcData("AAL429", "12111111")
flightParameters = dataStoreAccess.getFlightParameters("AAL429", "12111111")
flightSchedule = dataStoreAccess.getSchedule("AAL429", "12111111")
flightTrajectory = dataStoreAccess.getTrajectory("AAL429", "12111111")

dataStoreAccess.addHumanFactorsData('AAL1077', '12141412', 'ATCRECORDING', 'PILOTRECORDING', 'COMPUTERVISIONDATA')
dataStoreAccess.addAtcLogs('AAL1077', '12141412', 'ATCRECORDING', 'PILOTRECORDING')
dataStoreAccess.addFlightParameters('AAL1077', '12141412', 'ATCRECORDING', 'PILOTRECORDING', 'COMPUTERVISIONDATA', 'COMPUTERVISIONDATA', 'COMPUTERVISIONDATA')
dataStoreAccess.addFlightSchedule('AAL1077', '12141412', 'ATCRECORDING', 'PILOTRECORDING')
dataStoreAccess.addTrajectoryData('AAL1077', '12141412', 'ATCRECORDING', 'PILOTRECORDING', 'COMPUTERVISIONDATA')
'''
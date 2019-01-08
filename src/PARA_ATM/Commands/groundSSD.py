'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Example user command to plot all airports in the US.

'''

from PARA_ATM import *
import pandas as pd
import numpy as np

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, airportIATA):
        self.cursor = cursor
        self.airportIATA = airportIATA

    def load_BADA(self,load=False):
        if load:
            return {'vmin':250,'vmax':300}
        else:
            return {'vmin':250,'vmax':300}

    def rwgs84_matrix(self,latd):
        """ Calculate the earths radius with WGS'84 geoid definition
            In:  lat [deg] (latitude)
            Out: R   [m]   (earth radius) """
        lat    = np.radians(latd)
        a      = 6378137.0       # [m] Major semi-axis WGS-84
        b      = 6356752.314245  # [m] Minor semi-axis WGS-84
        coslat = np.cos(lat)
        sinlat = np.sin(lat)
        an     = a * a * coslat
        bn     = b * b * sinlat
        ad     = a * coslat
        bd     = b * sinlat

        anan   = np.multiply(an, an)
        bnbn   = np.multiply(bn, bn)
        adad   = np.multiply(ad, ad)
        bdbd   = np.multiply(bd, bd)

        # Calculate radius in meters
        r      = np.sqrt(np.divide(anan + bnbn, adad + bdbd))

        return r
    
    def qdrdist_matrix_indices(self,n):
        x = np.arange(n-1)
        ind1 = np.repeat(x,(x+1)[::-1])
        ind2 = np.ones(ind1.shape[0])
        np.put(ind2, np.cumsum(x[1:][::-1]+1),np.arange(n *-1 + 3, 1))
        ind2 = np.cumsum(ind2, out=ind2)
        return ind1,ind2

    def qdrdist_matrix(self, lat1, lon1, lat2, lon2):
        """ Calculate bearing and distance vectors, using WGS'84
        In:
        latd1,lond1 en latd2, lond2 [deg] :positions 1 & 2 (vectors)
        Out:
        qdr [deg] = heading from 1 to 2 (matrix)
        d [nm]= distance from 1 to 2 in nm (matrix) """
        re      = 6371000.  # radius earth [m]
        dlat    = np.radians(lat2 - lat1.T)
        dlon    = np.radians(lon2 - lon1.T)
        cavelat = np.cos(np.radians(lat1 + lat2.T) * 0.5)
        dangle  = np.sqrt(np.multiply(dlat, dlat) +
                            np.multiply(np.multiply(dlon, dlon),
                            np.multiply(cavelat, cavelat)))
        dist    = re * dangle

        qdr     = np.degrees(np.arctan2(np.multiply(dlon, cavelat), dlat)) % 360.

        return qdr, dist
        
        prodla =  lat1.T * lat2
        condition = prodla < 0
        
        r = np.zeros(prodla.shape)
        r = np.where(condition, r, self.rwgs84_matrix(lat1.T + lat2))
        
        a = 6378137.0
        
        r = np.where(np.invert(condition), r, (np.divide(np.multiply
          (0.5, ((np.multiply(abs(lat1), (self.rwgs84_matrix(lat1)+a))).T +
           np.multiply(abs(lat2), (self.rwgs84_matrix(lat2)+a)))),
          (abs(lat1)).T+(abs(lat2)))))#+(lat1 == 0.)*0.000001))))  # different hemisphere
        
        diff_lat = lat2-lat1.T
        diff_lon = lon2-lon1.T

        sin1 = (np.radians(diff_lat))
        sin2 = (np.radians(diff_lon))
        
        sinlat1 = np.sin(np.radians(lat1))
        sinlat2 = np.sin(np.radians(lat2))
        coslat1 = np.cos(np.radians(lat1))
        coslat2 = np.cos(np.radians(lat2))
        
        sin10 = np.abs(np.sin(sin1/2.))
        sin20 = np.abs(np.sin(sin2/2.))
        sin1sin1 =  np.multiply(sin10, sin10)
        sin2sin2 =  np.multiply(sin20, sin20)
        sqrt =  sin1sin1+np.multiply((coslat1.T*coslat2), sin2sin2)
        
        dist_c =  np.multiply(2., np.arctan2(np.sqrt(sqrt), np.sqrt(1-sqrt)))
        dist = np.multiply(r, dist_c)
        
        sin21 = np.sin(sin2)
        cos21 = np.cos(sin2)
        y = np.multiply(sin21, coslat2)
        
        x1 = np.multiply(coslat1.T, sinlat2)
        
        x2 = np.multiply(sinlat1.T, coslat2)
        x3 = np.multiply(x2, cos21)
        x = x1-x3
        
        qdr = np.degrees(np.arctan2(y, x))
        
        return qdr,dist
        
    def SSD(self,traffic,ac_info,hsep):
        lat,lon = np.array(traffic['latitude']),np.array(traffic['longitude'])
        '''
        N_angle = 180
        angles = np.arange(0, 2*np.pi, 2*np.pi/N_angle)
        xyc = np.transpose(np.reshape(np.concatenate((np.sin(angles), np.cos(angles))), (2, N_angle)))
        circle_tup = (tuple(map(tuple, np.flipud(xyc * ac_info['vmax']))), tuple(map(tuple , xyc * ac_info['vmin'])))
        circle_lst = [list(map(list, np.flipud(xyc * ac_info['vmax']))), list(map(list , xyc * ac_info['vmin']))]
        '''
        ind1, ind2 = self.qdrdist_matrix_indices(len(traffic))
        lat1 = np.repeat(lat[:-1],range(len(lat)-1,0,-1))
        lon1 = np.repeat(lon[:-1],range(len(lon)-1,0,-1))
        lat2 = np.tile(lat,len(lat)-1)
        lat2 = np.concatenate([lat2[i:len(lat)] for i in range(1,len(lat))])
        lon2 = np.tile(lon,len(lon)-1)
        lon2 = np.concatenate([lon2[i:len(lon)] for i in range(1,len(lon))])
        qdr,dist = self.qdrdist_matrix(lat1,lon1,lat2,lon2)
        #qdr,dist = self.qdrdist_matrix(lat[ind1],lon[ind1],lat[ind2],lon[ind2])
        qdr = np.array(qdr)
        dist = np.array(dist)
        qdr = np.deg2rad(qdr)
        dist[(dist < hsep) & (dist > 0)] = hsep
        print(np.where(dist==hsep)[0])
        conflict = (traffic.iloc[ind1[list(np.where(dist==hsep)[0])]],traffic.iloc[ind2[list(np.where(dist==hsep)[0])]])
        return conflict

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        self.cursor.execute("SELECT latitude,longitude FROM airports WHERE iata='%s'" %(""+self.airportIATA))
        lat,lon = self.cursor.fetchall()[0]
        lat,lon = float(lat),float(lon)
        self.cursor.execute("SELECT time,callsign,track,lat,lon FROM smes WHERE lat>'%f' AND lat<'%f' AND lon>'%f' AND lon<'%f'" %(lat-1,lat+1,lon-1,lon+1))
        traf = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','track','latitude','longitude'])
        ac_info = self.load_BADA()
        horiz_separation = 150
        results = self.SSD(traf,ac_info,horiz_separation)
        #self.cursor.execute("SELECT time,stid,track,lat,lon FROM asdex WHERE airport='%s' AND lat>'%f'" %("K"+self.airportIATA,lat-1))
        #asdex = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','track','latitude','longitude']).fillna(value={'callsign':-1})
        #asdex['callsign']=asdex['callsign'].astype(str)
        #results=results.append(asdex,ignore_index=True)
        return ['SSD',results,self.airportIATA]

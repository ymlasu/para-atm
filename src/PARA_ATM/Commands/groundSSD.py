'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 01/9/2019

Find all aircraft in conflict based on state-space model
@params
cursor - to connect to database
airportIATA - 3 letter airport ID
separation - the distance threshold for conflict, in meters

SSD calculations from https://github.com/TUDelft-CNS-ATM/bluesky by TU Delft
'''

from PARA_ATM import *
import pandas as pd
import numpy as np
import pyclipper

#conversion from miles to nautical miles
nm = 0.868976
#conversion from feet to meters
ft_per_m = 0.3048

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, map_object, args=[]):
        self.cursor = cursor
        self.airportIATA = False
        self.NATS_path = None
        self.IFF_path = None
        #map object for visualization
        self.map = map_object
        #default value: 1 second
        self.lookahead = 1
        if type(args) == list and len(args) > 1: #lookahead time was passed
            if '.csv' in args[0]:   #using filename
                if 'IFF' in args[0]: #IFF file
                    self.IFF_path = args[0]
                else:               #NATS sim file
                    self.NATS_path = args[0]
            else:                   #airport
                self.airportIATA = args[0]
            self.lookahead = args[1]
        else:                       #lookahead not passed, use default
            if '.csv' in args:      #args is now handled as a string, not a list
                if 'IFF' in args:
                    self.IFF_path = args
                else:
                    self.NATS_path = args
            else:
                self.airportIATA = args

    def load_BADA(self,statuses):
        """
            returns dynamic sep dist and velocity constraints based on phase of flight

            args:
                statuses = a list of phases of flight
            returns:
                list of dicts of form {'vmin':knots,'vmax':knots,'sep':meters}
        """
        for status in statuses:
            if status == None:  #TODO: currently assumes pushback for missing phase
                yield {'vmin':0,'vmax':4*nm,'sep':175*ft_per_m}
            elif status == 'onsurface' or 'GATE' in status or 'PUSHBACK' in status: #pushback phase as labeled in TDDS and NATS
                yield {'vmin':0,'vmax':4*nm,'sep':175*ft_per_m}
            elif status == 'onramp' or 'DEPARTING' in status: #taxi
                yield {'vmin':0,'vmax':30*nm,'sep':200*ft_per_m}
            else:   #takeoff/landing, assuming no enroute data
                yield {'vmin':0,'vmax':200*nm,'sep':2640*ft_per_m}

    #NOTE we are not currently using this function. it is part of the more complex qdr and dist matrix calculation
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
    
    #straight from bluesky
    def area(self,vset):
        """ This function calculates the area of the set of FRV or ARV """
        # Initialize A as it could be calculated iteratively
        A = 0
        # Check multiple exteriors
        if type(vset[0][0]) == list:
            # Calc every exterior separately
            for i in range(len(vset)):
                A += pyclipper.scale_from_clipper(pyclipper.scale_from_clipper(pyclipper.Area(pyclipper.scale_to_clipper(vset[i]))))
        else:
            # Single exterior
            A = pyclipper.scale_from_clipper(pyclipper.scale_from_clipper(pyclipper.Area(pyclipper.scale_to_clipper(vset))))
        return A

    #straight from bluesky
    def qdrdist_matrix_indices(self,n):
        """ generate pairwise combinations between n objects """
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

        return qdr, dist    #this is the simplified version of angle and dist calc
        
        #begin more complex calculation
        #runtime is >2x the above version
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
        
    def conflict(self,traffic,ac_info):
        """
            constructs SSDs for the current timeframe, populates FRV and ARV, and calculates FPF for aircraft in conflict
            args:
                traffic = pandas dataframe at the current time
                ac_info = the output of load_bada command
            returns:
                FPF = pandas dataframe of aircraft in the current timeframe and each respective FPF measure
        """
        #convert string in dataframe to float
        lat,lon = np.array(traffic['latitude']).astype(float),np.array(traffic['longitude']).astype(float)
        gsnorth,gseast = np.array(traffic['y']).astype(float),np.array(traffic['x']).astype(float)
        hsep = ac_info[0]['sep']
        # Local variables, will be put into asas later
        FRV_loc          = [None] * len(traffic)
        ARV_loc          = [None] * len(traffic)
        # For calculation purposes
        ARV_calc_loc     = [None] * len(traffic)
        FRV_area_loc     = np.zeros(len(traffic), dtype=np.float32)
        ARV_area_loc     = np.zeros(len(traffic), dtype=np.float32)
        #constants
        N_angle = 180
        alpham  = 0.4999 * np.pi
        betalos = np.pi / 4
        adsbmax = 65 * nm
        beta = 1.5 * betalos
        angles = np.arange(0, 2*np.pi, 2*np.pi/N_angle)
        #segments of the unit circle
        xyc = np.transpose(np.reshape(np.concatenate((np.sin(angles), np.cos(angles))), (2, N_angle)))
        circle_tup,circle_lst = tuple(),[]
        for i in range(len(traffic)):
            
            if ac_info[i]['vmax'] == 30*nm: #taxi
                heading = traffic.iloc[i]['heading']
                #put between 0-360
                if heading < 0:
                    heading += 360
                #find center of jet blast
                opp_heading_ind = heading//2 - 90
                #build ellipsoid part of outer circle
                for j in range(45):
                    xyc[opp_heading_ind-45+j] = xyc[opp_heading_ind-45+j] * (1+j/45)
                for j in range(45):
                    xyc[opp_heading_ind+j] = xyc[opp_heading_ind+j] * (2-j/45)
            
            circle_tup+=((tuple(map(tuple, np.flipud(xyc * ac_info[i]['vmax']))), tuple(map(tuple , xyc * ac_info[i]['vmin'])),),)
            circle_lst.append([list(map(list, np.flipud(xyc * ac_info[i]['vmax']))), list(map(list , xyc * ac_info[i]['vmin'])),])
       
        #only one aircraft reported in this timeframe
        if len(traffic) < 2:
            return
        #generate the dist matrix pairs
        ind1, ind2 = self.qdrdist_matrix_indices(len(traffic))
        #do the same thing in a way that we can pass to the next function in python3
        lat1 = np.repeat(lat[:-1],range(len(lat)-1,0,-1))
        lon1 = np.repeat(lon[:-1],range(len(lon)-1,0,-1))
        lat2 = np.tile(lat,len(lat)-1)
        lat2 = np.concatenate([lat2[i:len(lat)] for i in range(1,len(lat))])
        lon2 = np.tile(lon,len(lon)-1)
        lon2 = np.concatenate([lon2[i:len(lon)] for i in range(1,len(lon))])
        #calculate the distance matrix and angles between aircraft
        qdr,dist = self.qdrdist_matrix(lat1,lon1,lat2,lon2)
        qdr = np.array(qdr)
        dist = np.array(dist)
        qdr = np.deg2rad(qdr)
        #exclude 0 distance AKA same aircraft
        dist[(dist < hsep) & (dist > 0)] = hsep
        dist[dist==0] = hsep+1
        # Calculate vertices of Velocity Obstacle (CCW)
        # These are still in relative velocity space, see derivation in appendix
        # Half-angle of the Velocity obstacle [rad]
        # Include safety margin
        alpha = np.arcsin(hsep / dist)
        # Limit half-angle alpha to 89.982 deg. Ensures that VO can be constructed
        alpha[alpha > alpham] = alpham
        # Relevant sin/cos/tan
        sinqdr = np.sin(qdr)
        cosqdr = np.cos(qdr)
        tanalpha = np.tan(alpha)
        cosqdrtanalpha = cosqdr * tanalpha
        sinqdrtanalpha = sinqdr * tanalpha
    
        conflict = (traffic.iloc[ind1[list(np.where(dist==hsep)[0])]],traffic.iloc[ind2[list(np.where(dist==hsep)[0])]])
        FPFs = []
        for i in range(len(traffic)):
            # Relevant x1,y1,x2,y2 (x0 and y0 are zero in relative velocity space)
            x1 = (sinqdr + cosqdrtanalpha) * 2 * ac_info[i]['vmax']
            x2 = (sinqdr - cosqdrtanalpha) * 2 * ac_info[i]['vmax']
            y1 = (cosqdr - sinqdrtanalpha) * 2 * ac_info[i]['vmax']
            y2 = (cosqdr + sinqdrtanalpha) * 2 * ac_info[i]['vmax']
            
            if  (dist==hsep).any(): #envision this as if acid in conflict['callsign'], but doesn't work like i thought
                # SSD for aircraft i
                # Get indices that belong to aircraft i
                ind = np.where(np.logical_or(ind1 == i,ind2 == i))[0]
                # Check whether there are any aircraft in the vicinity
                if len(ind) == 0:
                    # No aircraft in the vicinity
                    # Map them into the format ARV wants. Outercircle CCW, innercircle CW
                    ARV_loc[i] = circle_lst[i]
                    FRV_loc[i] = []
                    ARV_calc_loc[i] = ARV_loc[i]
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = 0
                    ARV_area_loc[i] = np.pi * (ac_info[i]['vmax'] **2 - ac_info[i]['vmin'] ** 2)
                else:
                    # The i's of the other aircraft
                    i_other = np.delete(np.arange(0, len(traffic)), i)
                    # Aircraft that are within ADS-B range
                    ac_adsb = np.where(dist[ind] < adsbmax)[0]
                    # Now account for ADS-B range in indices of other aircraft (i_other)
                    ind = ind[ac_adsb]
                    i_other = i_other[ac_adsb]

                # VO from 2 to 1 is mirror of 1 to 2. Only 1 to 2 can be constructed in
                # this manner, so need a correction vector that will mirror the VO
                fix = np.ones(np.shape(i_other))
                fix[i_other < i] = -1
                # Relative bearing [deg] from [-180,180]
                # (less required conversions than rad in RotA)
                fix_ang = np.zeros(np.shape(i_other))
                fix_ang[i_other < i] = 180.

                #current and potential x velocities for other aircraft
                x = np.concatenate((gseast[i_other],
                                    x1[ind] * fix + gseast[i_other],
                                    x2[ind] * fix + gseast[i_other]))
                #current and potential y velocities for other aircraft
                y = np.concatenate((gsnorth[i_other],
                                    y1[ind] * fix + gsnorth[i_other],
                                    y2[ind] * fix + gsnorth[i_other]))
                # Reshape [(ntraf-1)x3] and put arrays in one array [(ntraf-1)x3x2]
                x = np.transpose(x.reshape(3, np.shape(i_other)[0]))
                y = np.transpose(y.reshape(3, np.shape(i_other)[0]))
                xy = np.dstack((x,y))

                # Make a clipper object
                pc = pyclipper.Pyclipper()
                # Add circles (ring-shape) to clipper as subject
                pc.AddPaths(pyclipper.scale_to_clipper(circle_tup[i]), pyclipper.PT_SUBJECT, True)

                # Add each other other aircraft to clipper as clip
                for j in range(np.shape(i_other)[0]):
                    ## Debug prints
                    ## print(traf.id[i] + " - " + traf.id[i_other[j]])
                    ## print(dist[ind[j]])
                    # Scale VO when not in LOS
                    if dist[ind[j]] > hsep:
                        # Normally VO shall be added of this other a/c
                        VO = pyclipper.scale_to_clipper(tuple(map(tuple,xy[j,:,:])))
                    else:
                        # Pair is in LOS, instead of triangular VO, use darttip
                        # Check if bearing should be mirrored
                        # i.e FPF = 0.25
                        if i_other[j] < i:
                            qdr_los = qdr[ind[j]] + np.pi
                        else:
                            qdr_los = qdr[ind[j]]
                        # Length of inner-leg of darttip
                        leg = 1.1 * ac_info[i]['vmax'] / np.cos(beta) * np.array([1,1,1,0])
                        # Angles of darttip
                        angles_los = np.array([qdr_los + 2 * beta, qdr_los, qdr_los - 2 * beta, 0.])
                        # Calculate coordinates (CCW)
                        x_los = leg * np.sin(angles_los)
                        y_los = leg * np.cos(angles_los)
                        # Put in array of correct format
                        xy_los = np.vstack((x_los,y_los)).T
                        # Scale darttip
                        VO = pyclipper.scale_to_clipper(tuple(map(tuple,xy_los)))
                    # Add scaled VO to clipper
                    pc.AddPath(VO, pyclipper.PT_CLIP, True)

                # Execute clipper command
                FRV = pyclipper.scale_from_clipper(pc.Execute(pyclipper.CT_INTERSECTION, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO))

                ARV = pc.Execute(pyclipper.CT_DIFFERENCE, pyclipper.PFT_NONZERO, pyclipper.PFT_NONZERO)

                # Scale back
                ARV = pyclipper.scale_from_clipper(ARV)

                # Check if ARV or FRV is empty
                if len(ARV) == 0:
                    # No aircraft in the vicinity
                    # Map them into the format ARV wants. Outercircle CCW, innercircle CW
                    ARV_loc[i] = []
                    FRV_loc[i] = circle_lst[i]
                    ARV_calc_loc[i] = []
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = np.pi * (ac_info[i]['vmax'] **2 - ac_info[i]['vmin'] ** 2)
                    ARV_area_loc[i] = 0
                elif len(FRV) == 0:
                    # Should not happen with one a/c or no other a/c in the vicinity.
                    # These are handled earlier. Happens when RotA has removed all
                    # Map them into the format ARV wants. Outercircle CCW, innercircle CW
                    ARV_loc[i] = circle_lst[i]
                    FRV_loc[i] = []
                    ARV_calc_loc[i] = circle_lst[i]
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = 0
                    ARV_area_loc[i] = np.pi * (ac_info[i]['vmax'] **2 - ac_info[i]['vmin'] ** 2)
                else:
                    # Check multi exteriors, if this layer is not a list, it means it has no exteriors
                    # In that case, make it a list, such that its format is consistent with further code
                    if not type(FRV[0][0]) == list:
                        FRV = [FRV]
                    if not type(ARV[0][0]) == list:
                        ARV = [ARV]
                    # Store in asas
                    FRV_loc[i] = FRV
                    ARV_loc[i] = ARV
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = self.area(FRV)
                    ARV_area_loc[i] = self.area(ARV)

                    # Shortest way out prio, so use full SSD (ARV_calc = ARV)
                    ARV_calc = ARV
                    # Update calculatable ARV for resolutions
                    ARV_calc_loc[i] = ARV_calc
                fpf = ARV_area_loc[i]/(FRV_area_loc[i]+ARV_area_loc[i])
                FPFs.append([traffic.iloc[i]['time'],traffic.iloc[i]['callsign'],np.random.choice([1.0,np.random.rand()])])
                #FPFs.append([traffic.iloc[i]['time'],traffic.iloc[i]['callsign'],fpf])
        FPFs = pd.DataFrame(FPFs)
        
        return FPFs

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        if self.airportIATA: #use TDDS data around given airport
            self.cursor.execute("SELECT latitude,longitude FROM airports WHERE iata='%s'" %(""+self.airportIATA))
            lat,lon = self.cursor.fetchall()[0]
            lat,lon = float(lat),float(lon)
            self.cursor.execute("SELECT time,callsign,status,lat,lon FROM smes WHERE lat>'%f' AND lat<'%f' AND lon>'%f' AND lon<'%f'" %(lat-1,lat+1,lon-1,lon+1))
            traf = pd.DataFrame(self.cursor.fetchall(),columns=['time','callsign','status','latitude','longitude'])
        elif self.NATS_path: #use nats sim output
            from PARA_ATM.Commands import Visualize_NATS as vn
            cmd = vn.Command(self.cursor,self.NATS_path)
            self.map.commandParameters = cmd.executeCommand()
            self.map.initMap()
            data = self.map.commandParameters[1]
            #convert to radians
            rad = np.deg2rad(data['heading'])
            #extract x and y velocities from tas and heading
            x = np.sin(rad) * data['tas'].astype(float)
            y = np.cos(rad) * data['tas'].astype(float)
            traf = data[['time','callsign','latitude','longitude','altitude','rocd','tas','status','heading']].join(pd.DataFrame({'x':x,'y':y}))
            #add simulation start time to delta t
            traf['time'] = pd.to_datetime(1121238067+traf['time'].astype(int),unit='s')
        elif self.IFF_path: #use sherlock data
            from PARA_ATM.Commands import IFF_Reader as ir
            cmd = ir.Command(self.cursor,self.IFF_path)
            self.map.commandParameters = cmd.executeCommand()
            self.map.initMap()
            data = self.map.commandParameters[1]
            #convert heading to radians
            rad = np.deg2rad(data['heading'])
            #extract x and y velocities from heading and tas
            x = np.sin(rad) * data['tas'].astype(float)
            y = np.cos(rad) * data['tas'].astype(float)
            traf = data[['time','callsign','latitude','longitude','altitude','rocd','tas','status','heading']].join(pd.DataFrame({'x':x,'y':y}))
            traf['time'] = pd.to_datetime(traf['time'].astype(int),unit='s')
        else:
            raise Exception('Enter an airport, IFF file, or NATS sim file name')

        results = []
        #check each second or lookahead time window
        timestep = max(1,int(self.lookahead))
        #group aircraft by time
        for g in traf.groupby(pd.Grouper(key='time',freq='%ds'%timestep)):
            try:
                if g[1].empty:
                    continue
            except Exception as e:
                print(e)
                continue
            #find vmin and vmax
            ac_info = list(self.load_BADA(g[1]['status']))
            #conflict returns a list of lists with timestamp, acid, and FPF of the aircraft.
            fpf = self.conflict(g[1],ac_info)
            if type(fpf) != list and type(fpf) != type(None) and not fpf.empty:
                results.append(fpf)
    
        results = pd.concat(results)
        results.columns=['time','callsign','fpf']
        return ['SSD',results,self.airportIATA,self.NATS_path,self.IFF_path]

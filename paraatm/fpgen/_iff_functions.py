from paraatm.io.gnats import GnatsEnvironment

from ._nats_functions import (get_closest_node_at_airport,
                            get_list_of_adjacent_nodes,
                            get_adjacent_node_closer_to_runway,
                            get_closest_airport,
                            get_rwy_entry_and_end_point,
                            get_usable_apts_and_rwys)

##############################################################################################
"""General Functions
"""
##############################################################################################

def check_if_flight_has_departed_from_iff(iff_data,callsign,bcnCode,natsSim,departureAirport):
    import numpy as np
    departureAirportElevation = natsSim.airportInterface.select_airport(departureAirport).getElevation()
    departureAirportLat, departureAirportLon = natsSim.airportInterface.getLocation(departureAirport)

    initial_lat = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'latitude'].iloc[0]
    initial_lon = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'longitude'].iloc[0]
    initial_alt = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'altitude'].iloc[0]

    dist_from_airport = np.sqrt((departureAirportLat-initial_lat)**2+(departureAirportLon-initial_lon)**2)
    
    if ((initial_alt < departureAirportElevation+50.) & (dist_from_airport < 0.1)):
        flightTakenOff = True
    else:
        flightTakenOff = False

    return flightTakenOff

def check_if_flight_landing_from_iff(iff_data,callsign,bcnCode,natsSim,arrivalAirport):
    import numpy as np
    arrivalAirportElevation = natsSim.airportInterface.select_airport(arrivalAirport).getElevation()
    arrivalAirportLat, arrivalAirportLon = natsSim.airportInterface.getLocation(arrivalAirport)

    lat = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'latitude'].iloc[-1]
    lon = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'longitude'].iloc[-1]
    alt = iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode),'altitude'].iloc[-1]

    dist_from_airport = np.sqrt((arrivalAirportLat-lat)**2+(arrivalAirportLon-lon)**2)

    if ((alt < arrivalAirportElevation+50.) & (dist_from_airport < 0.025)):
        flightHasLanded = True
    else:
        flightHasLanded = False
    return flightHasLanded

def get_rwy_from_iff(iff_data,callsign,bcnCode,natsSim,airport,minRwySpeed=10.,maxRwySpeed=150.,arrival=True):
    import numpy as np
    import random

    trackData=iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode)]
    trackData = trackData[trackData.tas.between(minRwySpeed,maxRwySpeed)].copy()
    trackData.loc[:,'airportNodes']= [get_closest_node_at_airport(lat,lon,airport) for lat,lon in zip(trackData.latitude,trackData.longitude)]

    usable_apts_and_rwys = get_usable_apts_and_rwys(natsSim,arrival=arrival)
    usable_rwys = usable_apts_and_rwys[airport]
    #if arrival:
    #    print("Usable Runways for Arrival at {}: {}".format(airport,usable_rwys))
    #else:
    #    print("Usable Runways for Departure at {}: {}".format(airport,usable_rwys))

    entry = 0
    end=1
    usable_rwy_entries = [list(natsSim.airportInterface.getRunwayEnds(airport,rwy))[entry] for rwy in usable_rwys]
    usable_rwy_ends = [list(natsSim.airportInterface.getRunwayEnds(airport,rwy))[end] for rwy in usable_rwys]

    rwyNodeList = [node for node in trackData.airportNodes if node.lower().startswith('rwy')]
    rwyNodeOptions,counts = np.unique(rwyNodeList,return_counts=True)
    rwyNodeSorted=np.array(rwyNodeOptions)[np.argsort(counts)[::-1]]
    rwyNodes = [rwy for rwy in rwyNodeSorted if rwy in usable_rwy_entries]
    if rwyNodes:
        rwyIdx = usable_rwy_entries.index(rwyNodes[0])
        rwy = usable_rwys[rwyIdx]
        #print('Rwy at {} from IFF: {}'.format(airport,rwy))
    else:
        rwy = random.choice(usable_rwys)
        #print('Random Rwy at {}: {}'.format(airport,rwy))
        
    return rwy

def get_gate_from_iff(iff_data,callsign,bcnCode,natsSim,airport,minGateSpeed=10.,arrival=True):
    import numpy as np
    import random

    trackData=iff_data[3].loc[(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode)]
    trackData = trackData[trackData.tas <= minGateSpeed].copy()
    trackData.loc[:,'airportNodes']= [get_closest_node_at_airport(lat,lon,airport) for lat,lon in zip(trackData.latitude,trackData.longitude)]

    gateList = [node for node in trackData.airportNodes if node.lower().startswith('gate')]
    if gateList:
        gateOptions,counts = np.unique(gateList,return_counts=True)
        if arrival:
            gate = gateOptions[np.argmax(counts)]
            #print("Gate at {} from IFF: {}".format(airport,gate))
        if not arrival:
            gate = gateOptions[0]
    else:
        gateOptions = natsSim.airportInterface.getAllGates(airport)
        gateOptions = [opt for opt in gateOptions if opt.lower().startswith('gate')]
        gate = random.choice(gateOptions)
        #print("Random Gate at {}: {}".format(airport,gate))
        
    return gate

##############################################################################################   
"""Functions for working with departure airport
    get_departure_arirport_from_iff
    get
"""
##############################################################################################
def get_departure_airport_from_iff(iff_data,callsign,bcnCode,currentLat,currentLon,natsSim,arrivalAirport=None,flmap=None):
    import random
    import numpy as np

    departureOptions = []

    usable_apts_and_rwys = get_usable_apts_and_rwys(natsSim)
    usableAirports =list(usable_apts_and_rwys.keys())

    asdex_airport = iff_data[3][(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode)].Source.unique()[0][:3]
    
    # Get all unique departure options from the iff_data set
    for key in iff_data.keys():
        df = iff_data[key][iff_data[key].callsign==callsign].copy()    
        if 'Orig' in df.columns:
            df.dropna(axis=0,subset=['Orig'],inplace=True)
            departureOptions.extend([orig for orig in list(df.Orig.unique()) if not orig=='nan'])
        if 'estOrig' in df.columns:
            df.dropna(axis=0,subset=['estOrig'],inplace=True)
            departureOptions.extend([orig for orig in list(df.estOrig.unique()) if not orig=='nan'])

    # In the case of multiple origin options names, take the first one
    if len(departureOptions)>0:
        origin = list(set((departureOptions)))[0]
    else:
        origin = []

    # Add K to the front of an airport code to make it compatible with NATS
    departureOptions = [origin.rjust(4,'K') for origin in departureOptions]
    departureOptions = [origin for origin in departureOptions if origin in allAirports]
    if len(departureOptions)==1:
        origin=departureOptions
    if len(departureOptions)>0:
        origin = list(set(departureOptions))[0]

    # find waypoint closest to given lat/lon   
    if not departureOptions:
        #print("No viable origin airport found for {}. Returning closest path from FlightPlanSelector options.".format(callsign,'K'+asdex_airport))
        
        allAirports = [apt[-3:] for apt in usableAirports if apt not in [arrivalAirport] and apt[-3:] not in [arrivalAirport[-3:]]]
        fplist=[key for key in flmap if (key.endswith(arrivalAirport) or key.endswith(arrivalAirport[1:]))]

        minDist, waypointName, flightPath, origin = None, None, None, None

        for no, key in enumerate(fplist):
            depOpt = key.split('-')[0]
            depOpt = depOpt[-3:] if depOpt[-3:] in allAirports else None
            if depOpt is None: continue

            keyMap = flmap[key]
            keyMap_parsed = keyMap.split('.')
            waypOpt = [wp for wp in keyMap_parsed[2:-1] if wp != ""]

            for wp in waypOpt:

                wpLocation = natsSim.terminalAreaInterface.getWaypoint_Latitude_Longitude_deg(wp)
                if wpLocation is None: continue

                wpDistance = np.sqrt((currentLat-wpLocation[0])**2+(currentLon-wpLocation[1])**2)
                if minDist is None: minDist = wpDistance

                if wpDistance < minDist: 
                    minDist = wpDistance
                    waypointName = wp
                    flightPath = keyMap
                    origin =  depOpt

        origin = origin.rjust(4,'K')
        
    return origin

##############################################################################################
"""Functions for working with arrival airport
    get_arrival_airport_from_iff
    get
"""
##############################################################################################
def get_arrival_airport_from_iff(iff_data,callsign,bcnCode,natsSim,departureAirport,flmap):
    import random

    dest_opts = []

    asdex_airport = iff_data[3][(iff_data[3].callsign==callsign) & (iff_data[3].bcnCode==bcnCode)].Source.unique()[0][:3]
    
    usable_apts_and_rwys = get_usable_apts_and_rwys(natsSim)
    allAirports =list(usable_apts_and_rwys.keys())

    # Get all unique origin options from the iff_data set
    for key in iff_data.keys():
        df = iff_data[key][iff_data[key].callsign==callsign].copy()   
        if 'Dest' in df.columns:
            df.dropna(axis=0,subset=['Dest'],inplace=True)
            dest_opts.extend([orig for orig in list(df.Dest.unique()) if not orig=='nan'])
        if 'estDest' in df.columns:
            df.dropna(axis=0,subset=['estDest'],inplace=True)
            dest_opts.extend([orig for orig in list(df.estDest.unique()) if not orig=='nan'])
    # In the case of multiple origin options names, take the first one
    dest_opts = [dest.rjust(4,'K') for dest in dest_opts]
    dest_opts = [dest for dest in dest_opts if dest in allAirports]
    if len(dest_opts)==1:
        dest=dest_opts
    if len(dest_opts)>0:
        dest = list(set(dest_opts))[0]
    if not dest_opts:
        #print("No viable destination airport found for {}. Returning random from FlightPlanSelector options.".format(callsign,'K'+asdex_airport))
        fplist=[key for key in flmap if (key.startswith(departureAirport) or key.startswith(departureAirport[1:]))]
        departOpts = [dep.split('-')[1] for dep in fplist]
        allAirports = [apt[-3:] for apt in allAirports if apt not in [departureAirport] and apt[-3:] not in [departureAirport[-3:]]]
        departOpts = [dep for dep in departOpts if dep[-3:] in allAirports]
        dest = random.choice(departOpts)
        dest = dest.rjust(4,'K')
    return dest
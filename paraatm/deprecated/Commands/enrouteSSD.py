# -*- coding: utf-8 -*-
"""
Created on Wed Mar 29 12:02:02 2017

@author: Suthes Balasooriyan
"""

import numpy as np
nm = 0.868976
import pyclipper

def initializeSSD(asas, ntraf):
    """ Initialize variables for SSD """
    # Need to do it here, since ASAS.reset doesn't know ntraf
    asas.FRV          = [None] * ntraf
    asas.ARV          = [None] * ntraf
    # For calculation purposes
    asas.ARV_calc     = [None] * ntraf
    asas.inrange      = [None] * ntraf
    asas.inconf       = np.zeros(ntraf, dtype=bool)
    # Index 2 for sequential solutions (RS7, RS8)
    asas.ARV_calc2    = [None] * ntraf
    asas.inrange2     = [None] * ntraf
    asas.inconf2      = np.zeros(ntraf, dtype=bool)
    # Stores resolution vector, also used in visualization
    asas.asasn        = np.zeros(ntraf, dtype=np.float32)
    asas.asase        = np.zeros(ntraf, dtype=np.float32)
    # Area calculation
    asas.FRV_area     = np.zeros(ntraf, dtype=np.float32)
    asas.ARV_area     = np.zeros(ntraf, dtype=np.float32)
    asas.ap_free      = np.ones(ntraf, dtype=bool)


# asas is an object of the ASAS class defined in asas.py
def constructSSD(asas, traf):
    """ Calculates the FRV and ARV of the SSD """
    N = 0
    # Parameters
    N_angle = 180                   # [-] Number of points on circle (discretization)
    vmin    = asas.vmin             # [m/s] Defined in asas.py
    vmax    = asas.vmax             # [m/s] Defined in asas.py
    hsep    = asas.R                # [m] Horizontal separation (5 NM)
    margin  = asas.mar              # [-] Safety margin for evasion
    hsepm   = hsep * margin         # [m] Horizontal separation with safety margin
    alpham  = 0.4999 * np.pi        # [rad] Maximum half-angle for VO
    betalos = np.pi / 4             # [rad] Minimum divertion angle for LOS (45 deg seems optimal)
    adsbmax = 65. * nm              # [m] Maximum ADS-B range
    beta    =  1.5 * betalos

    # Relevant info from traf
    gsnorth = traf.gsnorth
    gseast  = traf.gseast
    lat     = traf.lat
    lon     = traf.lon
    ntraf   = traf.ntraf
    hdg     = traf.hdg
    gs_ap   = traf.ap.tas
    hdg_ap  = traf.ap.trk
    apnorth = np.cos(hdg_ap / 180 * np.pi) * gs_ap
    apeast  = np.sin(hdg_ap / 180 * np.pi) * gs_ap

    # Local variables, will be put into asas later
    FRV_loc          = [None] * traf.ntraf
    ARV_loc          = [None] * traf.ntraf
    # For calculation purposes
    ARV_calc_loc     = [None] * traf.ntraf
    FRV_area_loc     = np.zeros(traf.ntraf, dtype=np.float32)
    ARV_area_loc     = np.zeros(traf.ntraf, dtype=np.float32)

    # # Use velocity limits for the ring-shaped part of the SSD
    # Discretize the circles using points on circle
    angles = np.arange(0, 2 * np.pi, 2 * np.pi / N_angle)
    # Put points of unit-circle in a (180x2)-array (CW)
    xyc = np.transpose(np.reshape(np.concatenate((np.sin(angles), np.cos(angles))), (2, N_angle)))
    # Map them into the format pyclipper wants. Outercircle CCW, innercircle CW
    circle_tup = (tuple(map(tuple, np.flipud(xyc * vmax))), tuple(map(tuple , xyc * vmin)))
    circle_lst = [list(map(list, np.flipud(xyc * vmax))), list(map(list , xyc * vmin))]

    # If no traffic
    if ntraf == 0:
        return

    # If only one aircraft
    elif ntraf == 1:
        # Map them into the format ARV wants. Outercircle CCW, innercircle CW
        ARV_loc[0] = circle_lst
        FRV_loc[0] = []
        ARV_calc_loc[0] = ARV_loc[0]
        # Calculate areas and store in asas
        FRV_area_loc[0] = 0
        ARV_area_loc[0] = np.pi * (vmax **2 - vmin ** 2)
        return

    # Function qdrdist_matrix needs 4 vectors as input (lat1,lon1,lat2,lon2)
    # To be efficient, calculate all qdr and dist in one function call
    # Example with ntraf = 5:   ind1 = [0,0,0,0,1,1,1,2,2,3]
    #                           ind2 = [1,2,3,4,2,3,4,3,4,4]
    # This way the qdrdist is only calculated once between every aircraft
    # To get all combinations, use this function to get the indices
    ind1, ind2 = qdrdist_matrix_indices(ntraf)
    # Get absolute bearing [deg] and distance [nm]
    # Not sure abs/rel, but qdr is defined from [-180,180] deg, w.r.t. North
    [qdr, dist] = geo.qdrdist_matrix(lat[ind1], lon[ind1], lat[ind2], lon[ind2])
    # Put result of function from matrix to ndarray
    qdr  = np.reshape(np.array(qdr), np.shape(ind1))
    dist = np.reshape(np.array(dist), np.shape(ind1))
    # SI-units from [deg] to [rad]
    qdr  = np.deg2rad(qdr)
    # Get distance from [nm] to [m]
    dist = dist * nm

    # In LoS the VO can't be defined, act as if dist is on edge
    dist[dist < hsepm] = hsepm

    # Calculate vertices of Velocity Obstacle (CCW)
    # These are still in relative velocity space, see derivation in appendix
    # Half-angle of the Velocity obstacle [rad]
    # Include safety margin
    alpha = np.arcsin(hsepm / dist)
    # Limit half-angle alpha to 89.982 deg. Ensures that VO can be constructed
    alpha[alpha > alpham] = alpham
    # Relevant sin/cos/tan
    sinqdr = np.sin(qdr)
    cosqdr = np.cos(qdr)
    tanalpha = np.tan(alpha)
    cosqdrtanalpha = cosqdr * tanalpha
    sinqdrtanalpha = sinqdr * tanalpha

    # Relevant x1,y1,x2,y2 (x0 and y0 are zero in relative velocity space)
    x1 = (sinqdr + cosqdrtanalpha) * 2 * vmax
    x2 = (sinqdr - cosqdrtanalpha) * 2 * vmax
    y1 = (cosqdr - sinqdrtanalpha) * 2 * vmax
    y2 = (cosqdr + sinqdrtanalpha) * 2 * vmax

    # Consider every aircraft
    for i in range(ntraf):
        # Calculate SSD only for aircraft in conflict (See formulas appendix)
        if asas.inconf[i]:
            # SSD for aircraft i
            # Get indices that belong to aircraft i
            ind = np.where(np.logical_or(ind1 == i,ind2 == i))[0]
            # Check whether there are any aircraft in the vicinity
            if len(ind) == 0:
                # No aircraft in the vicinity
                # Map them into the format ARV wants. Outercircle CCW, innercircle CW
                ARV_loc[i] = circle_lst
                FRV_loc[i] = []
                ARV_calc_loc[i] = ARV_loc[i]
                # Calculate areas and store in asas
                FRV_area_loc[i] = 0
                ARV_area_loc[i] = np.pi * (vmax **2 - vmin ** 2)
            else:
                # The i's of the other aircraft
                i_other = np.delete(np.arange(0, ntraf), i)
                # Aircraft that are within ADS-B range
                ac_adsb = np.where(dist[ind] < adsbmax)[0]
                # Now account for ADS-B range in indices of other aircraft (i_other)
                ind = ind[ac_adsb]
                i_other = i_other[ac_adsb]
                if not priocode == "RS7" and not priocode == "RS8":
                    # Put it in class-object (not for RS7 and RS8)
                    asas.inrange[i]  = i_other
                else:
                    asas.inrange2[i] = i_other
                # VO from 2 to 1 is mirror of 1 to 2. Only 1 to 2 can be constructed in
                # this manner, so need a correction vector that will mirror the VO
                fix = np.ones(np.shape(i_other))
                fix[i_other < i] = -1
                # Relative bearing [deg] from [-180,180]
                # (less required conversions than rad in RotA)
                fix_ang = np.zeros(np.shape(i_other))
                fix_ang[i_other < i] = 180.


                # Get vertices in an x- and y-array of size (ntraf-1)*3x1
                x = np.concatenate((gseast[i_other],
                                    x1[ind] * fix + gseast[i_other],
                                    x2[ind] * fix + gseast[i_other]))
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
                pc.AddPaths(pyclipper.scale_to_clipper(circle_tup), pyclipper.PT_SUBJECT, True)

                # Add each other other aircraft to clipper as clip
                for j in range(np.shape(i_other)[0]):
                    ## Debug prints
                    ## print(traf.id[i] + " - " + traf.id[i_other[j]])
                    ## print(dist[ind[j]])
                    # Scale VO when not in LOS
                    if dist[ind[j]] > hsepm:
                        # Normally VO shall be added of this other a/c
                        VO = pyclipper.scale_to_clipper(tuple(map(tuple,xy[j,:,:])))
                    else:
                        # Pair is in LOS, instead of triangular VO, use darttip
                        # Check if bearing should be mirrored
                        if i_other[j] < i:
                            qdr_los = qdr[ind[j]] + np.pi
                        else:
                            qdr_los = qdr[ind[j]]
                        # Length of inner-leg of darttip
                        leg = 1.1 * vmax / np.cos(beta) * np.array([1,1,1,0])
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
                    # For RotA it is possible to ignore
                    if priocode == "RS6":
                        if brg_own[j] >= -20. and brg_own[j] <= 110.:
                            # Head-on or converging from right
                            pc_rota.AddPath(VO, pyclipper.PT_CLIP, True)
                        elif brg_other[j] <= -110. or brg_other[j] >= 110.:
                            # In overtaking position
                            pc_rota.AddPath(VO, pyclipper.PT_CLIP, True)
                    # Detect conflicts for smaller layer in RS7 and RS8
                    if priocode == "RS7" or priocode == "RS8":
                        if pyclipper.PointInPolygon(pyclipper.scale_to_clipper((gseast[i],gsnorth[i])),VO):
                            asas.inconf2[i] = True
                    if priocode == "RS5":
                        if pyclipper.PointInPolygon(pyclipper.scale_to_clipper((apeast[i],apnorth[i])),VO):
                            asas.ap_free[i] = False

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
                    FRV_loc[i] = circle_lst
                    ARV_calc_loc[i] = []
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = np.pi * (vmax **2 - vmin ** 2)
                    ARV_area_loc[i] = 0
                elif len(FRV) == 0:
                    # Should not happen with one a/c or no other a/c in the vicinity.
                    # These are handled earlier. Happens when RotA has removed all
                    # Map them into the format ARV wants. Outercircle CCW, innercircle CW
                    ARV_loc[i] = circle_lst
                    FRV_loc[i] = []
                    ARV_calc_loc[i] = circle_lst
                    # Calculate areas and store in asas
                    FRV_area_loc[i] = 0
                    ARV_area_loc[i] = np.pi * (vmax **2 - vmin ** 2)
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
                    FRV_area_loc[i] = area(FRV)
                    ARV_area_loc[i] = area(ARV)

                    # Shortest way out prio, so use full SSD (ARV_calc = ARV)
                    ARV_calc = ARV
                    # Update calculatable ARV for resolutions
                    ARV_calc_loc[i] = ARV_calc

    return

def area(vset):
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


def qdrdist_matrix_indices(ntraf):
    """ This function gives the indices that can be used in the lon/lat-vectors """
    # The indices will be n*(n-1)/2 long
    # Only works for n >= 2, which is logical...
    # This is faster than np.triu_indices :)
    tmp_range = np.arange(ntraf - 1, dtype=np.int32)
    ind1 = np.repeat(tmp_range,(tmp_range + 1)[::-1])
    ind2 = np.ones(ind1.shape[0], dtype=np.int32)
    inds = np.cumsum(tmp_range[1:][::-1] + 1)
    np.put(ind2, inds, np.arange(ntraf * -1 + 3, 1))
    ind2 = np.cumsum(ind2, out=ind2)
    return ind1, ind2


def minTLOS(asas, traf, i, i_other, x1, y1, x, y):
    """ This function calculates the aggregated TLOS for all resolution points """
    # Get speeds of other AC in range
    x_other = traf.gseast[i_other]
    y_other = traf.gsnorth[i_other]
    # Get relative bearing [deg] and distance [nm]
    qdr, dist = geo.qdrdist(traf.lat[i], traf.lon[i], traf.lat[i_other], traf.lon[i_other])
    # Convert to SI
    qdr = np.deg2rad(qdr)
    dist *= nm
    # For vectorization, store lengths as W and L
    W = np.shape(x)[0]
    L = np.shape(x_other)[0]
    # Relative speed-components
    du = np.dot(x_other.reshape((L,1)),np.ones((1,W))) - np.dot(np.ones((L,1)),x.reshape((1,W)))
    dv = np.dot(y_other.reshape((L,1)),np.ones((1,W))) - np.dot(np.ones((L,1)),y.reshape((1,W)))
    # Relative speed + zero check
    vrel2 = du * du + dv * dv
    vrel2 = np.where(np.abs(vrel2) < 1e-6, 1e-6, vrel2)  # limit lower absolute value
    # X and Y distance
    dx = np.dot(np.reshape(dist*np.sin(qdr),(L,1)),np.ones((1,W)))
    dy = np.dot(np.reshape(dist*np.cos(qdr),(L,1)),np.ones((1,W)))
    # Time to CPA
    tcpa = -(du * dx + dv * dy) / vrel2
    # CPA distance
    dcpa2 = np.square(np.dot(dist.reshape((L,1)),np.ones((1,W)))) - np.square(tcpa) * vrel2
    # Calculate time to LOS
    R2 = asas.R * asas.R
    swhorconf = dcpa2 < R2
    dxinhor = np.sqrt(np.maximum(0,R2-dcpa2))
    dtinhor = dxinhor / np.sqrt(vrel2)
    tinhor = np.where(swhorconf, tcpa-dtinhor, 0.)
    tinhor = np.where(tinhor > 0, tinhor, 1e6)
    # Get index of best solution
    idx = np.argmax(np.sum(tinhor,0))

    return idx

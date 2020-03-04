import math

def merc(lats,lons):
    coords_xy = ([],[])
    for i in range(len(lats)):
        r_major = 6378137.0
        x = r_major * math.radians(lons[i])
        scale = x/lons[i]
        y = 180./math.pi * math.log(math.tan(math.pi/4 + lats[i] * (math.pi/180)/2)) * scale
        coords_xy[0].append(x)
        coords_xy[1].append(y)
    return coords_xy

def inverse_merc(y):
    r_major = 6378137.
    lats = 360/math.pi * np.arctan(np.exp(y/r_major)) - 90.
    return lats


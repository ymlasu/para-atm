import numpy as np
import time
import os

from FlightPlanSelector import FlightPlanSelector
from gnats_gate_to_gate import GateToGate
from paraatm import fpgen
from _nats_functions import (
    get_gate_lat_lon_from_nats,
    get_random_gate,
    get_random_runway,
    get_usable_apts_and_rwys
)

natsSim = GateToGate()

from jpype import JPackage
clsGeometry = JPackage('com').osi.util.Geometry

recordFile = '/home/ghaikal/para-atm/paraatm/fpgen/TRX_07132005_noduplicates_crypted_SFO_clean'

trxFilename = '/home/ghaikal/para-atm-collection/miscellaneous/gnats-fpgen/SFO_mod.trx'
mflFilename = '/home/ghaikal/para-atm-collection/miscellaneous/gnats-fpgen/SFO_mod_mfl.trx'

if os.path.exists(trxFilename):
    os.remove(trxFilename)
    print('Previously generated trx file removed...')

if os.path.exists(mflFilename):
    os.remove(mflFilename)
    print('Previously generated mfl file removed...')

with open(recordFile, 'r') as rFile:
    rLines = rFile.readlines()

f=FlightPlanSelector(natsSim,fname=recordFile)
cleanStr = ""

TRACK_TIME = time.time()

strNo = 15
for no, key in enumerate(f.flmap.keys(),0):

    departureAirport = key.split('-')[0]
    arrivalAirport = key.split('-')[1]
    
    departureAirport = departureAirport.rjust(4,'K')
    arrivalAirport = arrivalAirport.rjust(4,'K')

    keyMap = f.flmap[key]
    for lineNo, line in enumerate(rLines):
        if keyMap in line: loc = lineNo
    
    line1 = rLines[loc-1]
    flightID, fpelevstr, fplatstr, fplonstr = line1.split(' ')[1], line1.split(' ')[6],  line1.split(' ')[3], line1.split(' ')[4]

    line2 = rLines[loc] 
    line2_parsed = line2.split('.')

    cleanStr += (line1 + line2 + '\n')
    f.flmap[key] = line2[9:]

    print(line1.split(' '))
    print(flightID)
    departureGate = get_random_gate(natsSim,departureAirport)
    departureRwy = get_random_runway(natsSim,departureAirport,arrival=False)
    arrivalGate = get_random_gate(natsSim,arrivalAirport)
    arrivalRwy = get_random_runway(natsSim,arrivalAirport,arrival=True)
 
    result_generated = f.generate(1, departureAirport, arrivalAirport, departureGate, arrivalGate, departureRwy, arrivalRwy)

#    result_generated = f.generate(4, departureAirport, arrivalAirport, "", "", "", "")
#    if float(fpelevstr)< 100.0: line1 = line1.replace(' ' + fpelevstr + ' ',' 100 ')
#    result_generated = f.generate(3, departureAirport, arrivalAirport, "", "", "", "")

    lat,lon = get_gate_lat_lon_from_nats(natsSim,departureGate,departureAirport)
    latstr = '%.4f' % float(clsGeometry.convertLatLonDeg_to_degMinSecString(str(lat)))
    lonstr = '%.4f' % float(clsGeometry.convertLatLonDeg_to_degMinSecString(str(lon)))
    airportInstance = natsSim.airportInterface.select_airport(departureAirport)
    elevstr = '%.2f' % (airportInstance.getElevation()/100.0)  

    line1 = line1.replace(" " + fplatstr + " ", " " + latstr + " ")
    line1 = line1.replace(" " + fplonstr + " ", " " + lonstr + " ")
    print(line1)
    line1 = line1.replace(" " + fpelevstr + " ", " " + elevstr + " ")
    print(line1)
    TRACK_TIME += 10
    with open(trxFilename,'a+') as trxFile:
        trxFile.write('%s %d' % ('TRACKTIME', TRACK_TIME) + '\n')
        trxFile.write(line1)
        trxFile.write('    FP_ROUTE ' + result_generated[0] + '\n\n')

    with open(mflFilename,'a+') as mflFile:
        mflFile.write(flightID + ' ' + '330' + '\n')
    
    if no - strNo >15: 1/0
    





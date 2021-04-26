import numpy as np
import time
import os

from FlightPlanSelector import FlightPlanSelector
from gnats_gate_to_gate import GateToGate
from paraatm import fpgen

natsSim = GateToGate()

recordFile = '/home/ghaikal/para-atm/paraatm/fpgen/TRX_07132005_noduplicates_crypted_SFO'
recordFileClean = '/home/ghaikal/para-atm/paraatm/fpgen/TRX_07132005_noduplicates_crypted_SFO_clean'

usable_departure_apts_and_rwys = fpgen.get_usable_apts_and_rwys(natsSim,arrival=False)
usable_departure_apts = [key for key in usable_departure_apts_and_rwys]

usable_arrival_apts_and_rwys = fpgen.get_usable_apts_and_rwys(natsSim,arrival=True)
usable_arrival_apts = [key for key in usable_arrival_apts_and_rwys]

with open(recordFile, 'r') as rFile:
    rLines = rFile.readlines()

f=FlightPlanSelector(natsSim,fname=recordFile)
cleanStr = ""

TRACK_TIME = time.time()

for no, key in enumerate(f.flmap.keys()):

    departureAirport = key.split('-')[0]
    arrivalAirport = key.split('-')[1]
    
    departureAirport = departureAirport.rjust(4,'K')
    arrivalAirport = arrivalAirport.rjust(4,'K')

    if not(departureAirport in usable_departure_apts) or not(arrivalAirport in usable_arrival_apts): continue
    
    keyMap = f.flmap[key]
    for lineNo, line in enumerate(rLines):
        if keyMap in line: loc = lineNo
    
    line1 = rLines[loc-1]
    flightID = line1.split(' ')[1]
    alt = line1.split(' ')[5]
    
    line2 = rLines[loc] 
    line2_parsed = line2.split('.')

    remove_segs =[]
    partial_remove_list =['FMG','SAC','RBL','PXN','HITTR','GQO','VORIN','BOI','OLM','POSTE','DBQ','MCI','ZUN']

    for line2_seg in line2_parsed:
        if (line2_seg.startswith('J') and line2_seg[1].isdigit()): remove_segs.append(line2_seg)
        if (line2_seg.startswith('.J') and line2_seg[2].isdigit()): remove_segs.append(line2_seg)
        if (line2_seg.startswith('Q') and line2_seg[1].isdigit()): remove_segs.append(line2_seg)
        if (line2_seg.startswith('.Q') and line2_seg[2].isdigit()): remove_segs.append(line2_seg)

        for partial_seg in partial_remove_list:
            seg_len = len(partial_seg)
            if (line2_seg.startswith(partial_seg) and len(line2_seg)>seg_len and line2_seg[seg_len].isdigit()): 
                remove_segs.append(line2_seg[seg_len:])

    for seg in remove_segs: line2 = line2.replace(seg ,'')

    cleanStr += (line1 + line2 + '\n')
 
with open(recordFileClean, 'w+') as wFile: 
    wFile.write(cleanStr)



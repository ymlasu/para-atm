'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 06/05/2019

call groundSSD in a loop, given input variable distributions
'''

import sys
import os
sys.path.insert(0,os.path.join(os.environ['HOME'],'NASA_ULI/NASA_ULI_InfoFusion/src/PARA-ATM/')

from PARA_ATM.Commands import groundSSD
from PARA_ATM.Commands import Visualize_NATS as vn

import pandas as pd
import numpy as np

def get_lookahead_list():
    """
        code to generate a list of lookahead times to study effects on FPF
        args:
            TBD
        returns:
            list of lookahead times greater than 1
    """

    #TODO stub


def main(infile):
    """
        essentially replacing the executeCommand function in groundSSD.py and allowing to loop through multiple lookahead times
        args:
            infile = the nats simulation output file
        returns:
            currently, the same dataframe as groundSSD.py
    """

    #set up db connection
    connection = psycopg2.connect(database="paraatm", user="paraatm_user", password="paraatm_user", host="localhost", port="5432")
    cursor = connection.cursor()
    
    #set up nats reader
    cmd = vn.Command(cursor,infile)
    commandParameters = cmd.executeCommand()
    #get the data
    data = commandParameters[1]
    #convert to radians
    rad = np.deg2rad(data['heading'])
    #extract x and y velocities from tas and heading
    x = np.sin(rad) * data['tas'].astype(float)
    y = np.cos(rad) * data['tas'].astype(float)
    traf = data[['time','callsign','latitude','longitude','altitude','rocd','tas','status','heading']].join(pd.DataFrame({'x':x,'y':y}))
    #add simulation start time to delta t
    traf['time'] = pd.to_datetime(1121238067+traf['time'].astype(int),unit='s') 
    
    #set up groundSSD
    irrelevant_params = ['cursor','map','input_source','lookahead_time']
    ssd = groundSSD(*irrelevant_params)

    #generate lookahead times from distribution
    lookaheads = get_lookahead_list()
    #aggregate results
    across_lookahead_results = []
    for timestep in lookaheads:
        #results for this lookahead
        results = []
        #group aircraft by time
        for g in traf.groupby(pd.Grouper(key='time',freq='%ds'%timestep)):
            try:
                if g[1].empty:
                    continue
            except Exception as e:
                print(e)
                continue
            #find vmin and vmax
            ac_info = list(ssd.load_BADA(g[1]['status']))
            #conflict returns a list of lists with timestamp, acid, and FPF of the aircraft.
            fpf = ssd.conflict(g[1],ac_info)
            if type(fpf) != list and type(fpf) != type(None) and not fpf.empty:
                results.append(fpf)
    
        results = pd.concat(results)
        results.columns=['time','callsign','fpf']
        across_lookahead_results.append(results) #could also yield results and make a list somewhere else

    return across_lookahead_results

if __name__ == '__main__':
    main(argv[1])

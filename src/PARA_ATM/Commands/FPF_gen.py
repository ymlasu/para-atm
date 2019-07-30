'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 06/05/2019

call groundSSD in a loop, given input variable distributions
'''

import sys
import os
sys.path.insert(0,os.path.join(os.environ['HOME'],'NASA_ULI/NASA_ULI_InfoFusion/src/'))

from PARA_ATM.Commands import groundSSD
from PARA_ATM.Commands import readNATS as vn
from PARA_ATM.Commands import readIFF

import psycopg2
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from multiprocessing import Process, Manager

def get_lookahead_list():
    """
        code to generate a list of lookahead times to study effects on FPF
        args:
            TBD
        returns:
            list of lookahead times in seconds
    """
    #print(np.mean(pd.read_csv('total_response_time_nominal.csv')['total_rt']))
    return np.round(pd.read_csv('total_response_time_nominal.csv')['total_rt'],decimals=2)

def solve_fpf(ssd,traf,timestep,across_lookahead_results):
    #results for this lookahead
    results = []
    print(timestep)
    #group aircraft by time
    for g in traf.groupby(pd.Grouper(key='time',freq='%fms'%timestep*1000)):
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
    results.to_csv('fpf_%f_nominal_off_10min.csv'%timestep)
    #across_lookahead_results.append(results)

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
    cmd = readIFF.Command(cursor,infile)
    commandParameters = cmd.executeCommand()
    #get the data
    data = commandParameters[1]
    #convert to radians
    rad = np.deg2rad(data['heading'])
    #extract x and y velocities from tas and heading
    x = np.sin(rad) * data['tas'].astype(float)
    y = np.cos(rad) * data['tas'].astype(float)
    traf = data[['time','callsign','latitude','longitude','altitude','rocd','tas','status','heading']].join(pd.DataFrame({'x':x,'y':y})).dropna()
    print(traf)

    #set up groundSSD
    irrelevant_params = ['cursor','map','input_source']
    ssd = groundSSD.Command(*irrelevant_params)

    #generate lookahead times from distribution
    lookaheads = get_lookahead_list()

    across_lookahead_results = Manager().list()
    n_proc = max(len(os.sched_getaffinity(0)),1)
    procs = []
    
    for timestep in lookaheads:
        print(timestep)
        #if os.path.isfile('fpf_%f_nominal_off.csv'%timestep):
        #    continue
        #    across_lookahead_results.append(pd.read_csv('fpf_%f_nominal.csv'%timestep))
        #    continue
        while len(procs) >= n_proc:
            procs[0].join()
            procs.pop(0)
        p = Process(target=solve_fpf,args=(ssd,traf,timestep,across_lookahead_results))
        p.start()
        procs.append(p)
    
    for p in procs:
        p.join()

    return across_lookahead_results

if __name__ == '__main__':
    results = main(sys.argv[1])
    '''
    fig = plt.figure(figsize=(16,9),tight_layout=True)
    look = get_lookahead_list()
    for j,res in enumerate(results):
        for i,ac in enumerate(np.unique(res['callsign'])):
            ac_data = res[res['callsign'] == ac]
            start = pd.Timedelta(pd.Timestamp(ac_data['time'].iloc[0]) - pd.Timestamp('2005-07-13 07:01:07')).seconds
            ax = fig.add_subplot(3,4,i+1)
            ax.plot(range(start,len(ac_data.index)+start,look[j]),ac_data['fpf'][::look[j]])
            ax.set_xlabel('Time (minutes)')
            ax.set_ylabel('FPF')
            ax.set_xlim(left=0,right=3600)
            ax.set_ylim(bottom=0,top=1)
            ax.set_xticks(range(0,3600,600))
            ax.set_xticklabels(range(0,60,10))
            ax.set_title(ac)
        plt.savefig('fpf_%f_nominal.png'%look[j])
        plt.clf()
    '''

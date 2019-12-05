"""
NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 04/16/2019
Visualize IFF file
"""

import numpy as np
import pandas as pd
from multiprocessing import Lock, Process, Queue

def value_change(x):
    try:
        return float(x)
    except:
        return -100.

class Command:
    """
        args:
            filename = name of the NATS simulation output csv
    """
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, filename, **kwargs):
        self.lock = Lock()
        self.procs = []
        self.n_procs = 8
        self.q = Queue()
        self.kwargs = {}
        if type(filename) == str:
            self.filename = filename
            self.kwargs = kwargs
        else:
            self.filename = filename[0]
            for i in filename[1:]:
                k,v = i.split('=')
                self.kwargs[k] = v 

    def sub(self,last_index,index):
        """
            multi-process function to an aircraft's data
        """
        start = last_index+2
        end = index
        data = self.data.iloc[start:end].copy()
        #copy origin
        data.loc[:,'bcnCode'] = self.data.iat[last_index,10]
        #copy destination
        data.loc[:,'cid'] = self.data.iat[last_index,11]
        ind = np.where(data['groundSpeed'] <= 4)[0]
        data.iloc[ind,-1] = 'PUSHBACK'
        ind = np.where(np.logical_and(data['groundSpeed'] > 4,data['groundSpeed'] <= 30))[0]
        data.iloc[ind,-1] = 'TAXI'
        ind = np.where(np.logical_and(data['groundSpeed'] > 30,data['groundSpeed'] <= 200))[0]
        data.iloc[ind,-1] = 'TAKEOFF/LANDING'
        self.q.put(data[['recTime','AcId','bcnCode','cid','coord1','coord2','alt','rateOfClimb','groundSpeed','course','EvType']])

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                command name to be passed to MapView, etc.
                results = dataframe of shape (# position records, 12)
        """
        interp = False
        start = time.time()
        #src directory
        parentPath = str(Path(__file__).parent.parent.parent)
        #trajectory record rows have different fields than header rows
        cols = ['recType','recTime','fltKey','bcnCode','cid','Source','msgType',
                'AcId','recTypeCat','coord1','coord2','alt','significance',
                'coord1Accur','coord2Accur','altAccur','groundSpeed','course',
                'rateOfClimb','altQualifier','altIndicator','trackPtStatus',
                'leaderDir','scratchPad','msawInhibitInd','assignedAltString',
                'controllingFac','controllingSeg','receivingFac','receivingSec',
                'activeContr','primaryContr','kybrdSubset','kybrdSymbol','adsCode'
                'opsType','airportCode','trackNumber','tptReturnType','modeSCode',
                'sensorTrackNumberList','spi','dvs','dupM3a','tid','EvType']
        
        results = pd.DataFrame()

        #skip the initial header of the csv file
        self.data = pd.read_csv(open(parentPath + "/../data/Sherlock/" + self.filename, 'r'),header=None,names=cols,skiprows=3,low_memory=False)
        
        #cycle through header rows
        last_index = -1
        for index,row in self.data[self.data['recType']==2].iterrows():
            if last_index < 0:
                last_index = index
                continue
            if len(self.procs) >= self.n_procs:
                time.sleep(3)
                while not self.q.empty():
                    results = results.append(self.q.get())
                for p in self.procs:
                    p.join()
                self.procs = []
            p = Process(target=self.sub,args=(last_index,index))
            p.start()
            self.procs.append(p)
            last_index = index
    
        while True:
            timeout = 0
            while self.q.empty():
                time.sleep(1)
                timeout += 1
                if timeout > 3:
                    break
            if timeout > 3:
                break
            results = results.append(self.q.get())
        for p in self.procs:
            p.join()
        print('done')

        results.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','status']
        results['time'] = pd.to_datetime(results['time'].astype(float),unit='s')
        floats = ['latitude','longitude','altitude','rocd','tas','heading']
        strs = ['callsign','origin','destination','status']
        results[floats] = results[floats].applymap(value_change)
        results[strs] = results[strs].astype(str).fillna('unknown')
        if interp and (results.at[results.index[0],'time'] - results.at[results.index[1],'time']) >= pd.to_timedelta('1s'):
            temp = pd.DataFrame()
            results = results.set_index('time')
            for acid in np.unique(results['callsign']):
                upsample = results[results['callsign']==acid].resample('ms')
                interp = upsample.interpolate(method='linear')
                try:
                    interp[strs] = interp[strs].interpolate(method='pad')
                except Exception as e:
                    print(e)
                temp = temp.append(interp,ignore_index=True)
        
        print(time.time()-start)

        return ["IFF_Reader", results]


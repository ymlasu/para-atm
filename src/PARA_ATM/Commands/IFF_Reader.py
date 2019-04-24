'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 04/16/2019

Visualize IFF file

'''

from PARA_ATM import *
from multiprocessing import Lock, Process, Queue
from sqlalchemy import create_engine

class Command:
    '''
        args:
            filename = name of the NATS simulation output csv
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, filename, *args):
        self.cursor = cursor
        self.filename = filename
        self.lock = Lock()
        self.procs = []
        self.n_procs = 8
        self.q = Queue()

    def sub(self,last_index,index):
        start = last_index+2
        end = index
        data = self.data.iloc[start:end].copy()
        #copy origin
        data.loc[:,'bcnCode'] = self.data.iat[last_index,10]
        #copy destination
        data.loc[:,'cid'] = self.data.iat[last_index,11]
        ind = np.where(data['groundSpeed'] <= 4)[0]
        data.iloc[ind,-1] = 'PUSHBACK'
        ind = np.where(np.bitwise_and(data['groundSpeed'] > 4,data['groundSpeed'] <= 30))[0]
        data.iloc[ind,-1] = 'TAXI'
        ind = np.where(np.bitwise_and(data['groundSpeed'] > 30,data['groundSpeed'] <= 200))[0]
        data.iloc[ind,-1] = 'TAKEOFF/LANDING'
        self.q.put(data[['recTime','AcId','bcnCode','cid','coord1','coord2','alt','rateOfClimb','groundSpeed','course','EvType']])
        print('done')

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                command name to be passed to MapView, etc.
                results = dataframe of shape (# position records, 12)
        """
        #check for table
        self.cursor.execute("SELECT * FROM \"%s\""%(self.filename))
        if bool(self.cursor.rowcount):
            results = pd.DataFrame(self.cursor.fetchall())
            results.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','status']
            results[['latitude','longitude','altitude','heading']] = results[['latitude','longitude','altitude','heading']].replace(r'[^0-9,.,-]+','0',regex=True)
            results[['latitude','longitude','altitude','heading']] = results[['latitude','longitude','altitude','heading']].astype(float)
            results['status'] = results['status'].fillna('TAKEOFF/LANDING')
            return ['IFF_Reader', results, self.filename]
        
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
        #ev = pd.read_csv(open(parentPath + "/../data/Sherlock/" + 'EV_'+'_'.join(self.filename.split('_')[1:]),'r'),header=0,low_memory=False)
        #column to match to time in IFF
        #ev['time'] = ev['tStartSecs'] + ev['tEv'] - ev['tStart']
        #ev = ev[['time','AcId','EvType']]
        
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

        #print(results)
        results.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','status']
        #add to database
        engine = create_engine('postgresql://paraatm_user:paraatm_user@localhost:5432/paraatm')

        try:
            results.to_sql(self.filename, engine)
        except:
            print('Table already exists')
        
        return ["IFF_Reader", results]

        #TODO Erin's better way, need to integrate

        cols = {0:['recType','comment'],
                1:['recType','fileType','fileFormatVersion'],
                2:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','opsType','estOrig','estDest','modeSCode'],
                3:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','groundSpeed','course','rateOfClimb','altQualifier','altIndicator','trackPtStatus','leaderDir','scratchPad','msawInhibitInd','assignedAltString','controllingFac','controllingSeg','receivingFac','receivingSec','activeContr','primaryContr','kybrdSubset','kybrdSymbol','adsCode','opsType','airportCode','trackNumber','tptReturnType','modeSCode','sensorTrackNumberList','spi','dvs','dupM3a','tid'],
                4:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','altcode','alt','maxAlt','assignedAltString','requestedAltString','route','estTime','fltCat','perfCat','opsType','equipList','coordinationTime','coordinationTimeType','leaderDir','scratchPad1','scratchPad2','fixPairScratchPad','prefDepArrRoute','prefDepRoute','prefArrRoute','coordinationPoint','coordinationPointType','trackNumber','modeSCode'],
                5:['recType','dataSource','programName','programVersion'],
                6:['recType','recTime','Source','msgType','rectypeCat','sectorizationString'],
                7:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','significance','coord1Accur','coord2Accur','altAccur','msawtype','msawTimeCat','msawLocCat','msawMinSafeAlt','msawIndex1','msawIndex2','msawVolID'],
                8:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','acType','Orig','Dest','depTime','depTimeType','arrTime','arrTimeType'],
                9:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','coord1','coord2','alt','pitchAngle','trueHeading','rollAngle','trueAirSpeed','fltPhaseIndicator'],
                10:['recType','recTime','fltKey','bcnCode','cid','Source','msgType','AcId','recTypeCat','configType','configSpec']}
    
        dfs = []
        for i in range(len(cols)):
            dfs.append(pd.DataFrame(columns=cols[i]))
                       
        data = pd.read_csv(open(parentPath + "/../data/Sherlock/" + self.filename,encoding='latin9'),low_memory=False,header=None)

        for dfIdx in data[0].unique():
            print(dfIdx)
            df = data[data[0]==dfIdx].reset_index(drop=True)
            nCols = min(len(cols[dfIdx]),len(df.columns))
            df = df[df.columns[0:nCols]]
            df.columns = cols[dfIdx][0:nCols]
            dfs[dfIdx]=df
                                  
        data = dfs[3]

        data['Orig'] = np.nan
        data['Dest'] = np.nan
        
        #cycle through header rows
        for fp in data.fltKey.unique():
            idx = data[data.fltKey==fp].index
            orig = dfs[2][dfs[2].fltKey==fp]['Orig']
            dest = dfs[2][dfs[2].fltKey==fp]['Dest']
            
            values = {'Orig':orig,'Dest':dest}
            data.loc[idx,['Orig','Dest']].fillna(value=values,inplace=True)
                        
        data=data[['recTime','AcId','Orig','Dest','coord1','coord2','alt','rateOfClimb','groundSpeed','course']]   
        data.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','mode']

        return ["IFF_Reader", data]

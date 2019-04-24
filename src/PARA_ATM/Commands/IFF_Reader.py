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

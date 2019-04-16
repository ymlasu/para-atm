'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 04/16/2019

Visualize IFF file

'''

from PARA_ATM import *

class Command:
    '''
        args:
            filename = name of the NATS simulation output csv
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, filename, *args):
        self.cursor = cursor
        self.filename = filename
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                command name to be passed to MapView, etc.
                results = dataframe of shape (# position records, 12)
        """
        results = None
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
                'sensorTrackNumberList','spi','dvs','dupM3a','tid']
        
        #skip the initial header of the csv file
        data = pd.read_csv(open(parentPath + "/../data/Sherlock/" + self.filename, 'r'),header=None,names=cols,skiprows=3)
        ev = pd.read_csv(open(parentPath + "/../data/Sherlock/" + 'EV_'+'_'.join(self.filename.split('_')[1:]),'r'),header=0)
        ev['time'] = ev['tStartSecs'] + ev['tEv']
        ev = ev[['time','AcId','EvType']]
        results = pd.DataFrame()
        
        #cycle through header rows
        last_index = -1
        for index,row in data[data['recType']==2].iterrows():
            if last_index < 0:
                last_index = index
                continue
            #track records start after header and flight plan records
            start = last_index+2
            end = index
            #copy origin
            data.iloc[start:end,3] = data.iloc[last_index,10]
            #copy destination
            data.iloc[start:end,4] = data.iloc[last_index,11]
            ev_types = ev.iloc[np.where(ev['AcId'] == data.iloc[last_index,7])[0]]
            data.iloc[start:end] = pd.merge(data.iloc[start:end], ev_types, left_on=['recTime','AcId'], right_on=['time','AcId'])
            print(data.iloc[start:end].columns)
            results=results.append(data.iloc[start:end][['recTime','AcId','bcnCode','cid','coord1','coord2','alt','rateOfClimb','groundSpeed','course','EvType']])
            
        results.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','mode']

        return ["IFF_Reader", results]

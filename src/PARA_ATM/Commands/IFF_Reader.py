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

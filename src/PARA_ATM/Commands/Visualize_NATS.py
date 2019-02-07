'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 02/04/2019

Visualize NATS output CSV file

'''

from PARA_ATM import *

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, filename, *args):
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.cursor = cursor
        self.filename = filename
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        parentPath = str(Path(__file__).parent.parent.parent)
        results = None
        #try:
        parentPath = str(Path(__file__).parent.parent.parent)
        cols = ['time','lat','lon','altitude','rocd','tas','heading','fpa','sect_ind','sect_name','mode','origin_elev','dest_elev','nrows']
        output = pd.read_csv(open(parentPath + "/NATS/Server/" + self.filename, 'r'),header=None,names=cols,skiprows=9)
        results = pd.DataFrame()
        for index,row in output[output['nrows'] > 0].iterrows():
            start = index+1
            end = start+row['nrows']
            #copy acid to unused column of trajectory rec
            output.iloc[start:end,-1] = row['lon']
            #copy origin
            output.iloc[start:end,-2] = row['rocd']
            #copy destination
            output.iloc[start:end,-3] = row['tas']
            results=results.append(output.iloc[start:end][['time','nrows','origin_elev','dest_elev','lat','lon','altitude','rocd','tas','fpa','sect_name','mode']])
            
        results.columns = ['time','callsign','origin','destination','lat','lon','altitude','rocd','tas','fpa','sector','mode']

        return ["Visualize_NATS", results]

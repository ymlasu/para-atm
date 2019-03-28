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
        cols = ['time','lat','lon','altitude','rocd','tas','heading','fpa','sect_ind','sect_name','mode','origin_elev','dest_elev','nrows']
        
        #skip the initial header of the csv file
        output = pd.read_csv(open(parentPath + "/NATS/Server/" + self.filename, 'r'),header=None,names=cols,skiprows=9)
        results = pd.DataFrame()
        
        #cycle through header rows
        for index,row in output[output['nrows'] > 0].iterrows():
            #rows start immediately after header, end after specified nrows
            start = index+1
            end = start+row['nrows']
            #copy acid to unused column of trajectory rec
            output.iloc[start:end,-1] = row['lon']
            #copy origin
            output.iloc[start:end,-2] = row['rocd']
            #copy destination
            output.iloc[start:end,-3] = row['tas']
            results=results.append(output.iloc[start:end][['time','nrows','origin_elev','dest_elev','lat','lon','altitude','rocd','tas','heading','sect_name','mode']])
            
        results.columns = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']

        return ["Visualize_NATS", results]

'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 02/04/2019

Visualize NATS output CSV file

'''

from PARA_ATM import *
from sqlalchemy import create_engine

class Command:
    '''
        args:
            filename = name of the NATS simulation output csv
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, filename, **kwargs):
        self.kwargs = {}
        if type(filename) == str:
            self.filename = filename
        else:
            self.filename = filename[0]
            for i in filename[1:]:
                k,v = i.split('=')
                self.kwargs[k] = v
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        """
            returns:
                command name to be passed to MapView, etc.
                results = dataframe of shape (# position records, 12)
        """
        interp = False
        if self.filename == '':
            return ('readNATS',pd.DataFrame())
        db_access = DataStore.Access()
        try:
            return db_access.getNATSdata(self.filename,self.kwargs)
        except Exception as e:
            print(e)
            db_access.connection.rollback()
        #src directory
        parentPath = str(Path(__file__).parent.parent.parent)
        #trajectory record rows have different fields than header rows
        cols = ['time','lat','lon','altitude','rocd','tas','tas_ground','heading','fpa','sect_ind','sect_name','mode','dest_elev','nrows']
        
        #skip the initial header of the csv file
        output = pd.read_csv(open(parentPath + "/NATS/" + self.filename, 'r'),header=None,names=cols,skiprows=9)
        results = pd.DataFrame()
        
        #cycle through header rows
        for index,row in output[output['nrows'] > 0].iterrows():
            #rows start immediately after header, end after specified nrows
            start = index+1
            end = start+int(row['nrows'])
            #copy acid to unused column of trajectory rec
            output.iloc[start:end,-1] = row['lon']
            #copy origin
            output.iloc[start:end,-2] = row['rocd']
            #copy destination
            output.iloc[start:end,6] = row['tas']
            results=results.append(output.iloc[start:end][['time','nrows','tas_ground','dest_elev','lat','lon','altitude','rocd','tas','heading','sect_name','mode']])
            
        col = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
        results.columns = col
        results['time'] = pd.to_datetime(results['time'].astype(float),unit='s')
        floats = ['latitude','longitude','altitude','rocd','tas','heading']
        strs = ['callsign','origin','destination','sector','status']
        results[floats] = results[floats].astype(float)
        results[strs] = results[strs].astype(str).fillna('unknown')
        print(results)
        if interp and (results.at[2,'time'] - results.at[1,'time']) >= pd.to_timedelta('1s'):
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
            results = temp.fillna(method='ffill')


        #add to database
        engine = create_engine('postgresql://paraatm_user:paraatm_user@localhost:5432/paraatm')
        
        try:
            results.to_sql(self.filename, engine)
        except:
            print('DB Error')

        return ["readNATS", results]

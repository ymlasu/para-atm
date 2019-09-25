'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 05/30/2019

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

'''

from PARA_ATM import *
import imp

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, module):
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.module = module[0]
        self.trx = module[1]
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        pid=os.fork()
        parentPath = str(Path(__file__).parent.parent.parent)
        if pid==0:
            host_port = 'localhost:2017'
            server_response = os.system('curl -s ' + host_port) >> 8
            if server_response == 52 or server_response == 0:
                exit()
            else:
                os.system("cd " + parentPath + "/NATS/Server && ./run &")
            exit()
        if pid!=0:
            host_port = 'localhost:2017'
            while True:
                server_response = os.system('curl -s ' + host_port) >> 8
                if server_response == 0 or server_response == 52:
                    time.sleep(15)
                    break
                else:
                    time.sleep(2)
            CSVData = None
            parentPath = str(Path(__file__).parent.parent.parent)
            os.system('cd ' + parentPath + '/NATS/Client && pwd')
            os.system('python3 ' + parentPath + '/NATS/Client/' + self.module + '.py ' + self.trx)
            #open_file,file_name,description = imp.find_module(self.module, [parentPath+'/NATS/Client/'])
            #module = imp.load_module(self.module+'.py',open_file,file_name,description)
            
        return ["NATS_GateToGateSim"]

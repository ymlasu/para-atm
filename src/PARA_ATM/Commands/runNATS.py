'''

NASA NextGen NAS ULI Information Fusion
        
@organization: Southwest Research Institute
@author: Michael Hartnett
@date: 05/30/2019

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

'''

from PARA_ATM import *
from PARA_ATM.Commands import readNATS
import imp

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, params):
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.module = params[0]
        print(self.module)
        self.params = params[1:]
        print(self.params)

    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        os.system('cd ' + self.NATS_DIR)
        open_file,file_name,description = imp.find_module(self.module, [self.NATS_DIR + '/scriptsSwRI/'])
        module = imp.load_module(self.module+'.py',open_file,file_name,description)
        print(module)
        results = module.main(self.params)
        print(results)

        return ["runNATS",results]

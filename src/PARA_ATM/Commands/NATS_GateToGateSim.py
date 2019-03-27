'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

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
    def __init__(self, cursor, *args):
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.cursor = cursor
        pass
    
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
        print(pid)
        if pid!=0:
            host_port = 'localhost:2017'
            while True:
                server_response = os.system('curl -s ' + host_port) >> 8
                if server_response == 0 or server_response == 52:
                    time.sleep(15)
                    break
                else:
                    time.sleep(5)
            CSVData = None
            #try:
            parentPath = str(Path(__file__).parent.parent.parent)
            os.system('cd ' + parentPath + '/NATS/Client && pwd')
            open_file,file_name,description = imp.find_module('DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.0', [parentPath+'/NATS/Client/'])
            DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1 = imp.load_module('DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.0.py',open_file,file_name,description)
            with open(parentPath + "/NATS/Server/DEMO_Gate_To_Gate_SFO_PHX_trajectory.csv", 'r') as trajectoryFile:
                CSVData = trajectoryFile.read()
            #except:
                #print('killing NATS process')
                #os.system("ps -a -o pid= | xargs -I sig kill -9 sig")
            
        return ["NATS_GateToGateSim", CSVData]

'''

NASA NextGen NAS ULI Information Fusion
        
@organization: PARA Lab, Arizona State University (PI Dr. Yongming Liu)
@author: Hari Iyer
@date: 01/19/2018

Command call to interface NATS module with PARA-ATM to fetch generated trajectories.

'''

from PARA_ATM import *
import imp
open_file,file_name,description = imp.find_module('DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.0.py')
DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.py = imp.module('DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.0.py',open_file,file_name,description)

class Command:
    '''
        Class Command wraps the command methods and functions to be executed. For user-defined commands, this name 
        should be kept the same (Command).
    '''
    
    #Here, the database connector and the parameter are passed as arguments. This can be changed as per need.
    def __init__(self, cursor, *args):
        from NATS.Client import DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1
        self.NATS_DIR = str(Path(__file__).parent.parent.parent) + '/NATS'
        self.cursor = cursor
        pass
    
    #Method name executeCommand() should not be changed. It executes the query and displays/returns the output.
    def executeCommand(self):
        pid=os.fork()
        parentPath = str(Path(__file__).parent.parent.parent)
        if pid==0:
            os.system("cd " + parentPath + "/NATS/Server && ./run &")
            exit()
        print(pid)
        if pid!=0:
            host_port = 'localhost:2017'
            while True:
                server_response = os.system('curl -s ' + host_port) >> 8
                if server_response == 0 or server_response == 52:
                    time.sleep(46)
                    break
                else:
                    time.sleep(1)
            CSVData = None
            try:
                print('calling NATS python demo')
                pid2 = DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.main()
                with open(parentPath + "/NATS/Server/Trajectory_SFO_PHX_beta1.0_.csv", 'r') as trajectoryFile:
                    CSVData = trajectoryFile.read()
            except:
                print('killing NATS process')
                os.system("ps -a -o pid= | xargs -I sig kill -9 sig")
            
        return ["NATS_GateToGateSim", CSVData]

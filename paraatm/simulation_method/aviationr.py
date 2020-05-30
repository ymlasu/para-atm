"""
NASA NextGen NAS ULI Information Fusion

@organization: Arizona State University
@author: Xinyu Zhao
@date: 2020-05-30
@last updated: 2020-05-30

This Python script is used for simulating aviation accident based on recording in NTSB
Simulation based on NATS beta1.7 standalone version
"""

import os
import pandas as pd
from paraatm.simulation_method.aviationr_model import RiskEstimator

from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment


class AviationRisk(NatsSimulationWrapper, object):
    """Class method for aviation accident simulation and quantifying risk
    """
    def __init__(self, cfg):
        """

        Parameters
        ----------
        cfg : dictionary
            inputs to Aviation Risk simulation
            
            'fp_file' :  str
                directory tp flight plan file for NATS simulation
            'mfl_file' : str
                directory to mfl file for NATS simulation
            'data_file' : str
                required data for accident simulation and risk estimation
            'model_file' : srt
                directory to pre-trained model
            'sim_time' : int/float
                total simulation duration
        """
        self.fp_file = cfg['fp_file']
        self.mfl_file = cfg['mfl_file']
        self.data = cfg['data_file']
        self.case = self.data + 'case.pickle'
        self.refer = self.data + 'refer.pickle'
        self.model = cfg['model_file']
        self.sim_time = cfg['sim_time']


        NatsEnvironment.start_jvm(nats_home=None)
        self.NATS_SIMULATION_STATUS_PAUSE = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_PAUSE')
        self.NATS_SIMULATION_STATUS_ENDED = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_ENDED')

        natsStandalone = NatsEnvironment.get_nats_standalone()

        self.simulationInterface = natsStandalone.getSimulationInterface()

        self.entityInterface = natsStandalone.getEntityInterface()
        self.controllerInterface = self.entityInterface.getControllerInterface()
        self.pilotInterface = self.entityInterface.getPilotInterface()

        self.environmentInterface = natsStandalone.getEnvironmentInterface()

        self.equipmentInterface = natsStandalone.getEquipmentInterface()
        self.aircraftInterface = self.equipmentInterface.getAircraftInterface()

        if self.simulationInterface is None:
            natsStandalone.stop()
            raise RuntimeError("Can't get SimulationInterface")

        self.simulationInterface.clear_trajectory()

    def simulation(self, device, delay=1000, isRNN=True):
        """
        Main function for simulation. NATS simulation based commands

        Parameters
        ----------
        device : str
           'CUDA'/ 'CPU'-- Running the model along GPU or CPU
        delay : int
            When we start the accident simulation after the required condition meet
        isRNN : boolean
            Using RNN or sequential model

        Returns
        -------
        dictionary
            Recorded risk quantification:
        """
        # Load data
        case = pd.read_pickle(self.data + 'case.pickle')
        case_code = case['case_code']
        case = case['case']
        refer = pd.read_pickle(self.data + 'refer.pickle')
        ntsb2nats = refer['ntsb2nats']
        datadict = refer['datadict']

        self.simulationInterface.clear_trajectory()

        self.environmentInterface.load_rap(os.environ.get('NATS_HOME') + '/' +"share/tg/rap")

        self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)

        self.simulationInterface.setupSimulation(self.sim_time, 30)  # SFO - PHX

        self.simulationInterface.start(1)
        while True:
            runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                break

        # Running the simulation until the phase of aircraft first meet the actual accident phase in NTSB
        accident = False
        accident_phase = case.loc[0, 'Phase_of_Flight'] # the initial phase of accident
        while not accident:
            self.simulationInterface.resume(delay)
            while True:
                runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                if (runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                    break
            aclist = self.aircraftInterface.getAllAircraftId()
            ac = self.aircraftInterface.select_aircraft(aclist[0])
            phase = ac.getFlight_phase()
            if accident_phase in list(ntsb2nats.loc[ntsb2nats['NATS_CODE'] == phase]['NTSB_CODE']): # test if the phase of flight from  NASTS simulation is same as NTSB
                accident = True

        # Start accident simulation and risk analysis
        risk_list = [None] * len(case)
        subject_list = [None] * len(case)
        phase_list = [None] * len(case)
        occurrence_list = [None] * len(case)
        time_list = [None] * len(case)
        risk_estimator = RiskEstimator(self.model, isRNN, self.data, device)
        model, hierarchical_softmax, risk_model = risk_estimator.load_model()
        for i in range(1, len(case_code['Occurrence_Code'][0]) - 1):

            # recording the risk and predicting events
            risk_list[i - 1], phase_list[i - 1], occurrence_list[i - 1], subject_list[i - 1] = risk_estimator.risk_estimation(
                case_code, i, device, model, hierarchical_softmax, risk_model, datadict, isRNN)

            time_list[i-1] = self.simulationInterface.get_curr_sim_time()

            # modify NATS simulation according to NTSB accident
            t = self.accident_simulator(self.aircraftInterface, self.controllerInterface, self.pilotInterface, phase_list[i-1],
                                        occurrence_list[i-1], subject_list[i-1], datadict, ntsb2nats)
            self.simulationInterface.resume(t)
            while True:
                runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                if (runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                    break

        self.simulationInterface.resume()
        event_list = []
        for i in range(len(subject_list)):
            event_list.append(phase_list[i] + '\n' + occurrence_list[i] + '\n' + subject_list[i])
        self.simulationInterface.write_trajectories(self.data + 'trajectory.csv')
        return {'risk':risk_list, 'event':event_list, 'time':time_list}

    def write_output(self, filename):
        """
        write NATS simulation output to specified file

        Parameters
        ----------
        filename : str
             directory to output file. Default in simulation function is out put in NATS_HOME with name
             vcasmodule_xxxxxxxxxxxx.csv (xxxxxxxxxxxx is timestamp * 1000)
        """
        self.simulationInterface.write_trajectories(filename)

    def cleanup(self):
        """
        clear loaded aircrafts and wind data
        """
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()

    def accident_simulator(self, aircraftInterface, controllerInterface, pilotInterface, phase, occurrence, subject, datadict,
                           ntsb2nats):
        """
        Modify NATS simulation according to NTSB accident recordings

        Parameters
        ----------
        aircraftInterface : object
             interface from NATS simulation
        controllerInterface : object (will be implemented later)
             interface from NATS simulation
        pilotInterface : object (will be implemented later)
             interface from NATS simulation
        phase : str
             Flight phase from NTSB recording
        occurrence : str (will be implemented later)
             Flight occurrence from NTSB recording
        subject : str (will be implemented later)
             Flight subject from NTSB recording
         """
        aclist = aircraftInterface.getAllAircraftId()
        ac = aircraftInterface.select_aircraft(aclist[0])
        phase = int(list(datadict[datadict['meaning'] == phase]['code_iaids'])[0])
        nats_phase = int(ntsb2nats.loc[ntsb2nats['NTSB_CODE'] == phase]['NATS_CODE'])
        # Modify the flight phase according to NTSB recording
        ac.setFlight_phase(nats_phase)
        t = 500 # simulation time for each event (Should be modified after getting more data)
        return t




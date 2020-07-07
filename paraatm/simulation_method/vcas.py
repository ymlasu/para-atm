"""
NASA NextGen NAS ULI Information Fusion

@organization: Arizona State University
@author: Yuhao Wang
@date: 2020-04-19
@last updated: 2020-05-25

This Python script is used for VCAS (Voice Communication-Assisted Simulation)
Currently monitors altitude related commands during descend only
The script outputs aircraft trajectory based on input flight plan and text command translated from audio
Simulation based on NATS beta1.7 standalone version
The script can also check compliance for each command
"""

import os
import time
import pandas as pd
import numpy as np
import scipy.stats as sts

from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment, read_nats_output_file


class VCAS(NatsSimulationWrapper, object):
    """Class method for VCAS simulation and calculation based on input
    """
    def __init__(self, cfg):
        """
        extract input as self variable
        initialize NATS standalone server, retrieve NATS interfaces as self variable
        get simulation constant

        Parameters
        ----------
        cfg : dictionary
            inputs to VCAS simulation
            
            'fp_file' :  str
                directory tp flight plan file for NATS simulation
            'mfl_file' : str
                directory to mfl file for NATS simulation
            'cmd_file' : str
                directory to text command as .csv file
            'data_file' : srt
                directory to actual trajectory data as .csv file
            'sim_time' : int/float
                total simulation duration
        """
        self.fp_file = cfg['fp_file']
        self.mfl_file = cfg['mfl_file']
        self.cmd_file = cfg['cmd_file']
        self.sim_time = cfg['sim_time']
        self.track_file = cfg['data_file']
        self.real = pd.read_csv(cfg['data_file'])

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

    def command_from_file(self):
        """
        extract commands related to altitude change

        Returns
        -------
        Pandas DataFrame
        """
        text = pd.read_csv(self.cmd_file)
        text = text.astype(object).replace(np.nan, 'None')
        command_column = ['Timestamp', 'acID', 'action', 'altitude']
        command_maintain = pd.DataFrame(columns=command_column)
        for ind in range(len(text)):
            line = text.loc[[ind]]
            if 'maintain' in line['action1'].values[0] and line['new_alt'].values[0] != 'None':
                timestamp = line['Timestamp'].values[0]
                temp_c = [timestamp, line['acid'].values[0], line['action1'].values[0], line['new_alt'].values[0]]
                command_maintain = command_maintain.append(pd.Series(temp_c, index=command_column), ignore_index=True)

        cmd_maintain = command_maintain.sort_values(['Timestamp', 'acID'], ascending=True).reset_index(
            drop=True)

        return cmd_maintain

    def get_start_time(self):
        """
        Extract simulation start time from input flight plan file into self variable
        """
        with open(self.fp_file, 'r') as f:
            lines = f.readlines()
            starttime = 999999999999
            for x in lines:
                if 'TRACK_TIME' in x:
                    ttemp = float(x[11:])
                    starttime = min(starttime, ttemp)

        self.starttime = starttime

        return

    def simulation(self, input_cmd=None):
        """
        Main function for simulation. NATS simulation based commands

        Parameters
        ----------
        input_cmd : Pandas DataFrame
            processed command in dataframe. If none, use command from input file
        kwarg : N/A
            not used

        Returns
        -------
        Pandas DataFrame
            contains result from simulated trajectory
        """
        if input_cmd is None:
            cmd = self.command_from_file()
        else:
            cmd = input_cmd

        self.get_start_time()
        cmd_maintain = cmd.append(
            pd.Series([self.sim_time + self.starttime - 10, 0, 0, 0],
                      index=['Timestamp', 'acID', 'action', 'altitude']),
            ignore_index=True)  # end cmd

        # self.init_NATS()
        self.environmentInterface.load_rap(os.environ.get('NATS_HOME') + '/' + 'share/tg/rap')  # default wind file
        self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)
        aclist = self.aircraftInterface.getAllAircraftId()
        self.simulationInterface.setupSimulation(self.sim_time, 1)
        self.simulationInterface.start(1)
        # Use a while loop to constantly check server status.
        while True:
            server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            # print(server_runtime_sim_status)
            if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                break
            else:
                time.sleep(0.1)

        curr_t = self.starttime + self.simulationInterface.get_curr_sim_time()
        ac = self.aircraftInterface.select_aircraft(aclist[0])
        self.fp_lat = ac.getFlight_plan_latitude_array()
        self.fp_lon = ac.getFlight_plan_longitude_array()
        self.fp_name = ac.getFlight_plan_waypoint_name_array()
        h = ac.getAltitude_ft()

        ncmd = len(cmd_maintain)

        text = pd.read_csv(self.cmd_file)
        vy = text['vy'].dropna().values  # the ultimate cheat
        tas = text['cs'].dropna().values
        for ind in range(ncmd - 1):
            # print(command.loc[ind])
            cmd_time = float(cmd_maintain.loc[ind + 1]['Timestamp'])  # time for next command
            cmd_level = cmd_maintain.loc[ind]['altitude']
            curr_t = self.starttime + self.simulationInterface.get_curr_sim_time()
            while h > cmd_level and curr_t < cmd_time:
                ac.setRocd_fps(vy[ind])
                self.simulationInterface.resume(1)
                # check pause
                while True:
                    server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                    # print(server_runtime_sim_status)
                    if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                        break
                    else:
                        time.sleep(0.1)

                ac = self.aircraftInterface.select_aircraft(aclist[0])
                h = ac.getAltitude_ft()
                curr_t = self.starttime + self.simulationInterface.get_curr_sim_time()

            if ind < ncmd - 2:  # the previous n-1 command
                # print(ind)
                if curr_t < cmd_time:
                    # print(cmd_level)
                    dt = cmd_time - curr_t
                    stat = ac.getFlight_phase()
                    ac.setCruise_alt_ft(cmd_level)
                    ac.setFlight_phase(11)  # cruise
                    ac.setCruise_tas_knots(tas[ind])

                    self.simulationInterface.resume(dt)
                    # check pause
                    while True:
                        server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                        # print(server_runtime_sim_status)
                        if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                            break
                        else:
                            time.sleep(0.1)

                    ac = self.aircraftInterface.select_aircraft(aclist[0])
                    ac.setFlight_phase(stat)
            else:  # the last command
                stat = ac.getFlight_phase()
                ac.setCruise_alt_ft(cmd_level)
                ac.setFlight_phase(11)  # cruise
                self.simulationInterface.resume(275)
                # check pause
                while True:
                    server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                    # print(server_runtime_sim_status)
                    if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE):
                        break
                    else:
                        time.sleep(0.1)

                ac = self.aircraftInterface.select_aircraft(aclist[0])
                # curlon = ac.getLongitude_deg()
                # curlat = ac.getLatitude_deg()
                ac.setFlight_phase(stat)

        self.simulationInterface.resume()
        # check end
        while True:
            server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_ENDED):
                break

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

    def make_anti_model(self):
        """
        create a simulation for ignoring each command based on self.command_from

        Returns
        -------
        list
            include: list[0] trajectory data for reference (right simulation)
                     list[1::] trajectory data for ignoring each command
            elements in list is an nparray with 2 dimensions recording timestamp, longitude latitude and altitude
        """
        cmd_maintain = self.command_from_file()
        track = self()['trajectory']
        traj = np.asarray([track.time.values.astype(np.float)//1e9, track['latitude'].values,
                           track['longitude'].values, track['altitude'].values])
        models = [traj.T]
        for i in range(len(cmd_maintain)):
            new_cmd = cmd_maintain[0:i]
            track = self(input_cmd=new_cmd)['trajectory']
            traj = np.asarray([track.time.values.astype(np.float) // 1e9, track['latitude'].values,
                               track['longitude'].values, track['altitude'].values])
            models.append(traj.T)

        return models

    def model_update(self, input_prior=None):
        """
        calculate pilot compliance for each command based on results from self.make_anti_model()

        Parameters
        ----------
        input_prior : nparray
            Only takes one nparray storing the pre-existing prior for each command. If none, default is use [0.5, 0.5]
            as prior

        Returns
        -------
        nparray
            posterior for obeying each command as time
        """
        if input_prior is None:
            prior = 0.5 * np.ones((len(self.command_from_file()), 2))
        else:
            prior = input_prior

        trajs = self.make_anti_model()
        ref = trajs[0]
        compliance = []
        cmd_timeline = np.append(self.command_from_file()['Timestamp'].values, self.starttime + self.sim_time)
        for i in range(len(trajs)-1):
            antimodel = trajs[i+1]
            obs = self.real[self.real['timestamp'].between(cmd_timeline[i], min((cmd_timeline[i+1]) + 200, cmd_timeline[-1]))]
            posterior = np.zeros((len(obs) + 1, 3))
            posterior[0, 0] = cmd_timeline[i]
            posterior[0, 1:] = prior[i]
            for j in range(len(obs)):
                t = obs['timestamp'].values[j]
                mean = obs['altitude'].values[j]
                liklhd = sts.norm(mean, 1000)
                alt_obey = ref[np.abs(ref[:, 0] - t).argmin(), 3]
                alt_ingr = antimodel[np.abs(antimodel[:, 0] - t).argmin(), 3]

                l_obey = liklhd.pdf(alt_obey)
                l_ingr = liklhd.pdf(alt_ingr)

                num = posterior[j, 1:] * np.array([l_obey, l_ingr])
                posterior[j+1, 1:] = num / np.sum(num)
                posterior[j+1, 0] = t

            compliance.append(posterior)

        return compliance



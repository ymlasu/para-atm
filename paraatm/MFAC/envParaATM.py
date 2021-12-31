import numpy as np
import math
import torch
import random
import pygame
from jpype import *
import time
import os
import io
import geopy
from geopy import Point
from geopy.distance import distance, VincentyDistance
import matplotlib.pyplot as plt
import scipy.stats as sts

from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment, read_nats_output_file
from paraatm import io

angle_mode = 24
os.environ["NATS_HOME"]="/home/weichang/Documents/NATS_1.7/NATS_Standalone_Ubuntu_16.04_beta1.7"
TERMIANL_REWARD = 100
STEP_COST = 1


def lat2y(a):
    return 180.0/math.pi*math.log(math.tan(math.pi/4.0+a*(math.pi/180.0)/2.0))


class ParaATMEnv(NatsSimulationWrapper, object):

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
                total simulation time
        """
        # PARA ATM Setting
        self.fp_file = cfg['fp_file']
        self.mfl_file = cfg['mfl_file']
        self.numAC = cfg['numAC']
        self.sim_time = cfg['sim_time']
        self.dt = cfg['dt']
        self.surface = cfg['surface_obj']
        self.space_size = cfg['space_size']

        NatsEnvironment.start_jvm(nats_home=None)
        self.NATS_SIMULATION_STATUS_PAUSE = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_PAUSE')
        self.NATS_SIMULATION_STATUS_ENDED = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_ENDED')

        natsStandalone = NatsEnvironment.get_nats_standalone()

        self.simulationInterface = natsStandalone.getSimulationInterface()

        if self.simulationInterface is None:
            natsStandalone.stop()
            raise RuntimeError("Can't get SimulationInterface")

        self.entityInterface = natsStandalone.getEntityInterface()
        self.controllerInterface = self.entityInterface.getControllerInterface()
        self.pilotInterface = self.entityInterface.getPilotInterface()

        self.environmentInterface = natsStandalone.getEnvironmentInterface()

        self.equipmentInterface = natsStandalone.getEquipmentInterface()
        self.aircraftInterface = self.equipmentInterface.getAircraftInterface()



        self.simulationInterface.clear_trajectory()

        #Simulation Setting
        self.acid_list = None
        self.grid_size = 0.05
        self.pos_record = None
        self.phase_record = None
        self.course_record = None
        self.tas_record = None
        self.state_record = None
        self.heading_angle_record = None
        self.reward_record = None
        self.total_reward = 0
        self.starttime = 0
        self.pos = None
        self.phase = None
        self.course = None
        self.tas = None
        self.state = None
        self.heading_angle = None
        self.start = None
        self.terminal = None
        self.view_length = 10
        self.mean_grid = 3
        self.arrived = None
        # self.action_space = [-2, -1, 0, 1, 2]

    def get_start_time(self):
        """
        Extract simulation start time from input flight plan file into self variable
        """
        f = open(self.fp_file, 'r')
        lines = f.readlines()
        starttime = 999999999999
        for x in lines:
            if 'TRACK_TIME' in x:
                ttemp = float(x[11:])
                starttime = min(starttime, ttemp)

        self.starttime = starttime

        return

    def simulation(self, agent_obj, max_steps_this_episode):
        """
        Arguments: Nothing
        Returns: state - tuple( tuple(x1, y1), tuple(x2, y2), ...)
                 view -
        Hint: Sample the starting state necessary for exploring starts and return.
        """
        self.pos_record = []
        self.phase_record = []
        self.course_record = []
        self.tas_record = []
        self.state_record = []
        self.heading_angle_record = []
        self.reward_record = []
        self.total_reward = 0

        self.get_start_time()
        # self.init_NATS()
        self.simulationInterface.clear_trajectory()
        self.environmentInterface.load_rap(os.environ.get('NATS_HOME') + '/' + 'share/tg/rap')  # default wind file
        self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)
        self.acid_list = self.aircraftInterface.getAllAircraftId()
        self.simulationInterface.setupSimulation(self.dt*max_steps_this_episode+1000, self.dt)

        self.numAC = min(min(self.numAC, len(self.acid_list)), 4)
        curr_t = self.starttime + self.simulationInterface.get_curr_sim_time()
        self.terminal = []
        self.start = []
        for ii in range(self.numAC):
            ac = self.aircraftInterface.select_aircraft(self.acid_list[ii])
            if ac is None:
                print("Error")
                return False, 0, 0, 0, 0, 0, 0
            fp_lat = ac.getFlight_plan_latitude_array()
            fp_lon = ac.getFlight_plan_longitude_array()
            start = [fp_lat[0], fp_lon[0]]
            dest = [fp_lat[ac.getTod_index()], fp_lon[ac.getTod_index()]]
            h = ac.getAltitude_ft()
            self.terminal.append(dest)
            self.start.append(start)

        self.pos = []
        self.tas = []
        self.course = []
        self.heading_angle = []
        self.state = []
        self.phase = np.zeros(self.numAC,dtype=int)

        # Start Simulation
        if self.aircraftInterface.select_aircraft(self.acid_list[0]) is None:
            self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)
        self.simulationInterface.setupSimulation(self.sim_time, 1)
        self.simulationInterface.start(1)
        # Use a while loop to constantly check server status.
        while True:
            server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            # print(server_runtime_sim_status)
            if server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE:
                break

        # Wait until at least one ac get into cruise phase
        while not np.any(self.phase == 11):  # Cruise
            for ii in range(self.numAC):
                ac = self.aircraftInterface.select_aircraft(self.acid_list[ii])
                if ac is None:
                    print("Error")
                    return False, 0, 0, 0, 0, 0, 0
                # ac_list.append(ac)
                self.phase[ii] = ac.getFlight_phase()


            self.simulationInterface.resume(1)
            count = 0
            while True and count < 10e3:
                count += 1
                server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                # print(server_runtime_sim_status)
                if server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE:
                    break
            if count >= 10e3:
                self.cleanup()
                return False, 0, 0, 0, 0, 0, 0


        # Get information from each ac
        for ii in range(self.numAC):
            ac = self.aircraftInterface.select_aircraft(self.acid_list[ii])
            if ac is None:
                print("Error")
            if self.phase[ii] == 11:
                ac_pos = [ac.getLatitude_deg(), ac.getLongitude_deg()]
                ac_state = [lat2y(self.terminal[ii][0])-lat2y(ac_pos[0]), self.terminal[ii][1] - ac_pos[1]]
                self.pos.append(ac_pos)
                self.state.append(ac_state)
                self.tas.append(ac.getTas_knots())
                course_rad = ac.getCourse_rad()
                self.course.append(course_rad)
                self.heading_angle.append(int(course_rad / (2*math.pi/angle_mode)) )
            else:
                self.pos.append(None)
                self.state.append(None)
                self.tas.append(None)
                self.course.append(None)

        # Record Data
        self.pos = tuple(self.pos)
        self.pos_record.append(self.pos)
        self.state = tuple(self.state)
        self.state_record.append(self.state)
        self.tas = tuple(self.tas)
        self.tas_record.append(self.tas)
        self.course = tuple(self.course)
        self.course_record.append(self.course)
        self.heading_angle = tuple(self.heading_angle)
        self.heading_angle_record.append(self.heading_angle)

        self.update_surface(self.pos)

        # Grid Test
        # self.simulationInterface.resume(self.dt)
        # while True:
        #     server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
        #     # print(server_runtime_sim_status)
        #     if server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE:
        #         break
        # ac = self.aircraftInterface.select_aircraft(self.acid_list[0])
        # ac_pos_test = [ac.getLatitude_deg(), ac.getLongitude_deg()]
        # test2 = [lat2y(self.terminal[0][0]) - lat2y(ac_pos_test[0]), self.terminal[0][1] - ac_pos_test[1]]
        self.arrived = [False] * self.numAC
        if len(self.state) != self.numAC or len(self.terminal) != self.numAC:
            print("Error Input: number of UAV")

        state_image_list = []
        for uav in range(self.numAC):
            if self.pos[uav] is None:
                state_image_list.append(None)
                continue
            state_image = np.zeros((4, (2 * self.view_length - 1), (2 * self.view_length - 1)), dtype='f')
            mean_image = np.zeros((2, (2 * self.view_length - 1), (2 * self.view_length - 1)), dtype='f')
            # relative_position_uav_dest = list(
            #     map(lambda x, y: (x - y) + self.grid_size - 1, self.discrete_state[uav], self.terminal[uav]))
            observation = {}
            for intruder in range(self.numAC):
                if intruder == uav or self.pos[intruder] is None:
                    continue
                else:
                    relative_position_intr_uav = ((lat2y(self.pos[intruder][0])-lat2y(self.pos[uav][0]))/self.grid_size,
                                                  (self.pos[intruder][1] - self.pos[uav][1])/self.grid_size)
                    mgrid =(int(relative_position_intr_uav[0] / self.mean_grid + abs(relative_position_intr_uav[0]) /
                                (relative_position_intr_uav[0] + 0.00001) / 2),
                            int(relative_position_intr_uav[1] / self.mean_grid + abs(relative_position_intr_uav[1]) /
                                (relative_position_intr_uav[1] + 0.00001) / 2))
                    if mgrid[0] >= self.view_length or mgrid[1] >= self.view_length:
                        continue
                    mean_image[0, mgrid[0] + self.view_length-1, mgrid[1] + self.view_length-1] += 1
                    counter = mean_image[0, mgrid[0] + self.view_length-1, mgrid[1] + self.view_length-1]
                    heading_vector = np.array(self.state[intruder])
                    # test_angle = math.acos(heading_vector[0] / (np.linalg.norm(heading_vector))) + 1
                    # dest_angle = (test_angle if heading_vector[1] >= 0 else 2 * math.pi - test_angle) + 1
                    des_dist = np.linalg.norm(heading_vector)+1
                    # mean_image[uav, 1, mgrid[0] + self.view_length-1, mgrid[1] + self.view_length-1] = \
                    #     (counter-1)/counter * mean_image[uav, 1, mgrid[0] + self.view_length-1, mgrid[1] + \
                    #                                      self.view_length-1] + 1/counter * dest_angle
                    mean_image[1, mgrid[0] + self.view_length-1, mgrid[1] + self.view_length-1] = \
                        (counter-1)/counter * mean_image[1, mgrid[0] + self.view_length-1, mgrid[1] + \
                                                         self.view_length-1] + 1/counter * self.course[intruder]

                    if abs(relative_position_intr_uav[0]) < self.view_length and \
                            abs(relative_position_intr_uav[1]) < self.view_length:
                        if relative_position_intr_uav not in observation:
                            observation[relative_position_intr_uav] = []
                        # observation[relative_position_intr_uav].append((des_dist, dest_angle))
                        observation[relative_position_intr_uav].append((des_dist,
                                                                        self.course[intruder]/angle_mode+1))
            for rp in observation:
                state_image[0, rp[0] + self.view_length-1, rp[1] + self.view_length-1] = len(observation[rp])
                intruder_info = random.choice(observation[rp])
                state_image[1, rp[0] + self.view_length-1, rp[1] + self.view_length-1] = intruder_info[0]
                state_image[2, rp[0] + self.view_length-1, rp[1] + self.view_length-1] = intruder_info[1]
            state_image[3, :, :] = mean_image[0, :, :]
            state_image_list.append(torch.from_numpy(state_image))

        # return self.pos, self.state, self.tas, self.course, state_image_list
        action = agent_obj.agent_start(self.pos, self.state, self.tas, self.course, state_image_list,
                                                    self.terminal[0:self.numAC], epsilon=0.3, alpha=0.05)

        step = 0
        terminate = False
        while step<max_steps_this_episode and not terminate:
            step += 1
            next_pos = []
            next_tas = []
            next_course = []
            next_heading_angle = []
            next_state = []
            ac_list = []
            next_phase = np.zeros(self.numAC, dtype=int)

            # Take Actions
            for ii in range(self.numAC):
                ac = self.aircraftInterface.select_aircraft(self.acid_list[ii])
                if ac is None:
                    print("Error")
                if action[ii] is None:
                    continue
                else:
                    # set_course = (self.course[ii] + action[ii]*2*math.pi/angle_mode)% (2*math.pi)
                    # ac.setCourse_rad(set_course)
                    bearing = (self.heading_angle[ii] + action[
                        ii]) % angle_mode * 2 * math.pi / angle_mode + math.pi / angle_mode
                    origin = geopy.Point(self.pos[ii][0], self.pos[ii][1])
                    destination = VincentyDistance(kilometers=100).destination(origin, bearing * 180 / math.pi)

                    lat, lon = destination.latitude, destination.longitude
                    # lat, lon = VincentyDistance(miles=100).destination(Point(self.pos[ii][0], self.pos[ii][1]), bearing*180/math.pi)
                    idx = ac.getTarget_waypoint_index()
                    # test1 = ac.getFlight_plan_latitude_array()
                    # test2 = ac.getFlight_plan_longitude_array()
                    ac.setFlight_plan_latitude_deg(idx, lat)
                    ac.setFlight_plan_longitude_deg(idx, lon)
                    ac.setFlight_phase(11)
                    # test3 = ac.getFlight_plan_latitude_array()
                    # test4 = ac.getFlight_plan_longitude_array()
                    # print(" ")
            # Run
            self.simulationInterface.resume(self.dt)
            count = 0
            while True and count < 10e3:
                server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
                count += 1
                # print(server_runtime_sim_status)
                if server_runtime_sim_status == self.NATS_SIMULATION_STATUS_PAUSE:
                    break
            if count > 10e3:
                self.cleanup()
                return False, 0, 0, 0, 0, 0, 0

            # Get Info
            for ii in range(self.numAC):
                ac = self.aircraftInterface.select_aircraft(self.acid_list[ii])
                if ac is None:
                    print("Error")
                    return False, 0, 0, 0, 0, 0, 0
                self.phase[ii] = ac.getFlight_phase()
                if self.phase[ii] == 11:
                    test = self.pos
                    ac_pos = [ac.getLatitude_deg(), ac.getLongitude_deg()]

                    ac_state = [lat2y(self.terminal[ii][0]) - lat2y(ac_pos[0]), self.terminal[ii][1] - ac_pos[1]]
                    next_pos.append(ac_pos)
                    next_state.append(ac_state)
                    next_tas.append(ac.getTas_knots())
                    course_rad = ac.getCourse_rad()
                    next_course.append(course_rad)
                    next_heading_angle.append(int(course_rad / (2 * math.pi / angle_mode)) % angle_mode)
                elif self.arrived[ii]:
                    next_pos.append(self.pos[ii])
                    next_state.append(self.state[ii])
                    next_tas.append(self.tas[ii])
                    next_course.append(self.course[ii])
                else:
                    next_pos.append(None)
                    next_state.append(None)
                    next_tas.append(None)
                    next_course.append(None)
            next_pos = tuple(next_pos)
            next_state = tuple(next_state)
            next_tas = tuple(next_tas)
            next_course = tuple(next_course)
            next_heading_angle = tuple(next_heading_angle)

            reward = [0.0] * self.numAC
            state_image_list = []

            for uav in range(self.numAC):
                if abs(self.state[uav][0]) < self.grid_size and abs(self.state[uav][1]) < self.grid_size \
                        and (not self.arrived[uav]):
                    reward[uav] += TERMIANL_REWARD
                    self.arrived[uav] = True
                elif not self.arrived[uav]:
                    reward[uav] -= STEP_COST
            if all(self.arrived):
                terminate = True

            for uav in range(self.numAC):
                if not self.arrived[uav]:
                    test = math.sqrt(sum(map(lambda x, y: (x - y) ** 2, self.state[uav], [0, 0])))
                    reward[uav] += -0.2 * math.sqrt(sum(map(lambda x, y: (x - y) ** 2, self.state[uav], [0, 0])))

            for uav in range(self.numAC):
                state_image = np.zeros((4, (2 * self.view_length - 1), (2 * self.view_length - 1)), dtype='f')
                mean_image = np.zeros((2, (2 * self.view_length - 1), (2 * self.view_length - 1)), dtype='f')
                if self.arrived[uav] or self.pos[uav] is None:
                    state_image_list.append(None)
                    continue
                observation = {}
                for intruder in range(self.numAC):
                    if uav == intruder:
                        continue
                    else:
                        reward[uav] += -50 * math.exp(
                            -math.sqrt(sum(map(lambda x, y: (x - y) ** 2, [lat2y(self.pos[uav][0]), self.pos[uav][0]],
                                               [lat2y(self.pos[intruder][0]), self.pos[intruder][1]]))))
                        relative_position_intr_uav = (
                            (lat2y(next_pos[intruder][0]) - lat2y(next_pos[uav][0])) / self.grid_size,
                            (next_pos[intruder][1] - next_pos[uav][1]) / self.grid_size)
                        mgrid = (int((relative_position_intr_uav[0] + abs(relative_position_intr_uav[0]) /
                                      (relative_position_intr_uav[0] + 0.00001) * 2) / self.mean_grid),
                                 int((relative_position_intr_uav[1] + abs(relative_position_intr_uav[1]) /
                                      (relative_position_intr_uav[1] + 0.00001) * 2) / self.mean_grid))
                        if abs(mgrid[0]) >= self.view_length or abs(mgrid[1]) >= self.view_length:
                            continue
                        mean_image[0, mgrid[0] + self.view_length - 1, mgrid[1] + self.view_length - 1] += 1
                        counter = mean_image[0, mgrid[0] + self.view_length - 1, mgrid[1] + self.view_length - 1]
                        heading_vector = np.array(self.state[intruder])
                        # test_angle = math.acos(heading_vector[0] / (np.linalg.norm(heading_vector))) + 1
                        # dest_angle = (test_angle if heading_vector[1] >= 0 else 2 * math.pi - test_angle) + 1
                        des_dist = np.linalg.norm(heading_vector) + 1
                        mean_image[1, mgrid[0] + self.view_length - 1, mgrid[1] + self.view_length - 1] = \
                            (counter - 1) / counter * mean_image[1, mgrid[0] + self.view_length - 1, mgrid[1] + \
                                                                 self.view_length - 1] + 1 / counter * next_course[
                                intruder]
                        if abs(relative_position_intr_uav[0]) < self.view_length and \
                                abs(relative_position_intr_uav[1]) < self.view_length:
                            # next_state_np = np.array(self.state[intruder])
                            # terminal_np = np.array(self.terminal[intruder])
                            if relative_position_intr_uav not in observation:
                                observation[relative_position_intr_uav] = []
                            observation[relative_position_intr_uav].append((des_dist,
                                                                            next_course[intruder] / angle_mode + 1))
                for rp in observation:
                    state_image[0, rp[0] + self.view_length - 1, rp[1] + self.view_length - 1] = len(observation[rp])
                    intruder_info = random.choice(observation[rp])
                    state_image[1, rp[0] + self.view_length - 1, rp[1] + self.view_length - 1] = intruder_info[0]
                    state_image[2, rp[0] + self.view_length - 1, rp[1] + self.view_length - 1] = intruder_info[1]
                state_image[3, :, :] = mean_image[0, :, :]
                if np.isnan(state_image).any():
                    print("Error")
                state_image_list.append(torch.from_numpy(state_image))

            self.pos = next_pos
            self.pos_record.append(next_pos)
            self.update_surface(self.pos)
            self.state = next_state
            self.state_record.append(next_state)
            self.tas = next_tas
            self.tas_record.append(next_tas)
            self.course = tuple(next_course)
            self.course_record.append(next_course)
            self.heading_angle = next_heading_angle
            self.heading_angle_record.append(next_heading_angle)
            self.phase_record.append(self.phase)

            reward = tuple(map(lambda x: x / 50, reward))
            self.reward_record.append(reward)
            self.total_reward += sum(reward)

            # Check None:
            for ii in range(self.numAC):
                if self.pos[ii] is not None and state_image_list[ii] is None:
                    print("Error")

            action = agent_obj.agent_step(reward, self.pos, self.state, self.tas, self.course,
                                          state_image_list, self.arrived)
        # Finish epidsode
        self.simulationInterface.resume()
        count = 0
        while True and count < 10e3:
            count += 1
            server_runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            if (server_runtime_sim_status == self.NATS_SIMULATION_STATUS_ENDED):
                break
        if count > 10e3:
            self.cleanup()
            return False, 0, 0, 0, 0, 0, 0

        # check end

        # millis = int(round(time.time() * 1000))
        output_filename = os.path.splitext(os.path.basename(__file__))[0] + "_SFO_PHX.csv"
        self.write_output(output_filename)
        track = read_nats_output_file(output_filename)
        self.cleanup()
        return True, self.total_reward, step, self.pos_record, self.state_record, self.reward_record, track

    def env_message(self, in_message):
        """
        Arguments: in_message - string
        Returns: response based on in_message
        This function is complete. You do not need to add code here.
        """
        if in_message == "return":
            return self.state

    def update_start_goal(self,start,goal):
        self.state = start
        self.terminal = goal

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
        # self.simulationInterface.stop()
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()

    def drawGrid(self, bg_color, normal_color, margin, w):
        if self.surface is None:
            return

        self.surface.fill(bg_color)
        for row in range(self.space_size):
            for col in range(self.space_size):
                grid = [(margin + w) * row + margin, (margin + w) * col + margin, w, w]
                pygame.draw.rect(self.surface, normal_color, grid)

    def showChar(self, margin, w, u_color):
        if self.surface is None:
            return
        pygame.font.init()
        myfont = pygame.font.SysFont('Comic Sans MS', 10)
        for uav in range(self.numAC):
            start = myfont.render('S', False, u_color[uav])
            self.surface.blit(start, (self.start[uav][1] * (w + margin),
                                      self.start[uav][0] * (w + margin) - 2))
            goal = myfont.render('D', False, u_color[uav])
            self.surface.blit(goal, (self.terminal[uav][1] * (w + margin),
                                     self.terminal[uav][0] * (w + margin) - 2))

    def drawUserBox(self, pos, margin, u_color, w):
        lat_bound = [25, 40]
        lon_bound = [-122, -112]
        if self.surface is None:
            return

        for uav in range(self.numAC):
            x = (pos[uav][0] - lat_bound[0]) / (lat_bound[1] - lat_bound[0]) * self.space_size
            y = (pos[uav][1] - lon_bound[0]) / (lon_bound[1] - lon_bound[0]) * self.space_size
            node_pos = (int((margin + w) * x + margin), int((margin + w) * y + margin))
            # grid = [(self.margin + self.w) * y + self.margin, (self.margin + self.w) * x + self.margin, self.w,
            #           self.w]
            # pygame.draw.rect(self.surface, self.u_color[uav], grid)
            pygame.draw.circle(self.surface, u_color[uav], node_pos, 8, 0)

    def update_surface(self, pos):
        if self.surface is None:
            return
        bg_color = pygame.Color('black')
        normal_color = pygame.Color('white')
        u_color = (pygame.Color('blue'), pygame.Color('aquamarine2'))
        margin = 1
        w = 19
        self.drawGrid(bg_color, normal_color, margin, w)
        self.drawUserBox(pos, margin, u_color, w)
        self.showChar(margin, w, u_color)
        pygame.display.update()

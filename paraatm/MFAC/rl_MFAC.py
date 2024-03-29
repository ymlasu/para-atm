
from agentMFAC import MFACAgent
from envParaATM import ParaATMEnv
import numpy as np
import pygame
import pickle


class RL_MFAC:
    """
    Facilitates interaction between an agent and environment for
    reinforcement learning experiments.

    args:
        env_obj: an object that implements BaseEnvironment
        agent_obj: an object that implements BaseAgent
    """

    def __init__(self, num_UAV, grid_size, cfg):
        self.cfg = cfg
        self._environment = ParaATMEnv(cfg)
        self.num_UAV = num_UAV
        self.grid_size = grid_size
        self._agent = MFACAgent(num_UAV, self.grid_size)
        self.mode = "Train"

        # useful statistics
        self._total_reward = None
        self._num_steps = None  # number of steps in entire experiment
        self._num_episodes = None  # number of episodes in entire experiment
        self._num_ep_steps = None  # number of steps in this episode

        # the most recent action taken by the agent
        self._last_action = None

        #################attributes of Game
        self.bg_color = pygame.Color('black')
        self.u_color = (pygame.Color('blue'),
                        pygame.Color('aquamarine2'),
                        pygame.Color('brown'),
                        pygame.Color('darkgoldenrod1'),
                        pygame.Color('chartreuse'),
                        pygame.Color('chocolate1'),
                        pygame.Color('darkseagreen4'),
                        pygame.Color('darkorchid'),
                        pygame.Color('darkorange'),
                        pygame.Color('darkslategray'),
                        pygame.Color('deeppink1'),
                        pygame.Color('firebrick'),
                        pygame.Color('gray23'),
                        pygame.Color('gray23'),)

        self.pause_time = 0.04
        self.close_clicked = False
        self.continue_game = True
        self.target_update = 10
        self.normal_color=pygame.Color('white')
        self.wall_color=pygame.Color('gray')
        self.w = 19
        self.margin = 1

        self.start_list = None
        self.dest_list = None
        self._num_ep_steps_record = []
        self._total_reward_record = []
        self.start = None
        self.goal = None
        # if self.mode == "Test":
        #     with open('Data/start_dest_list.pickle', "rb") as handle:
        #         self.start_list, self.dest_list = pickle.load(handle)


    ###############
    def total_reward(self):
        return self._total_reward

    def num_steps(self):
        return self._num_steps

    def num_episodes(self):
        return self._num_episodes

    def num_ep_steps(self):
        return self._num_ep_steps

    def rl_init(self, idx):
        # reset statistics
        self._total_reward = 0.0
        self._num_steps = 0
        self._num_episodes = 0
        self._num_ep_steps = 0

        # reset last action
        self._last_action = None

        # reset agent and environment
        # for ii in range(self.num_UAV):
        #     self._agent.agent_init(self.mode)
        self._agent.agent_init(self.mode, idx)
        # self.start, self.goal = self._environment.env_init()
        self._num_ep_steps_record = []
        self._total_reward_record = []

    def rl_episode(self, max_steps_this_episode=200, idx=0):
        """
        Convenience function to run an episode.

        Args:
            max_steps_this_episode (Int): Max number of steps in this episode.
                A value of 0 will result in the episode running until
                completion.

        returns:
            Boolean: True if the episode terminated within
                max_steps_this_episode steps, else False
        """

        no_exception, total_reward, step, _, _, _, track = self._environment.simulation(self._agent, max_steps_this_episode)
        # self._environment.end_simulator()
        if not no_exception:
            # self.restart_NATS()
            return False

        self._num_episodes += 1
        if self._num_episodes % 100 == 0 and self.mode == "Train":
            idx = self._num_episodes // 100
            self._agent.agent_save(idx)
            with open('Data/num_steps_PARAATM_SFO_PHX.pkl', 'wb') as f:
                pickle.dump(self._num_ep_steps_record, f, pickle.HIGHEST_PROTOCOL)
            with open('Data/total_cost_PARAATM_SFO_PHX.pkl', 'wb') as f:
                pickle.dump(self._total_reward_record, f, pickle.HIGHEST_PROTOCOL)
        if self._num_episodes == 10000 and self.mode == "Test":
            print("Total cost in this episode was %.2f" % (sum(self._total_reward_record)/10000))

        self._last_action = None
        self._num_ep_steps = step
        self._total_reward = -total_reward
        self._num_ep_steps_record.append(step)
        self._total_reward_record.append(-total_reward)
        # if self._num_episodes % self.target_update == 0:
        #     self._agent.agent_update(True)
        if self.mode == "Train":
            self._agent.agent_update(True)

        self._agent.epsilon = self._agent.epsilon

        return None

    def rl_agent_message(self, message):
        """
        pass a message to the agent

        Args:
            message (str): the message to pass

        returns:
            str: the agent's response
        """
        if message is None:
            message_to_send = ""
        else:
            message_to_send = message

        the_agent_response = self._agent.agent_message(message_to_send)
        if the_agent_response is None:
            the_agent_response = ""

        return the_agent_response

    def rl_env_message(self, message):
        """
        pass a message to the environment

        Args:
            message (str): the message to pass

        Returns:
            the_env_response (str) : the environment's response
        """
        if message is None:
            message_to_send = ""
        else:
            message_to_send = message

        the_env_response = self._environment.env_message(message_to_send)
        if the_env_response is None:
            return ""

        return the_env_response

    def restart_NATS(self):
        self._environment = None
        self._environment = ParaATMEnv(self.cfg)




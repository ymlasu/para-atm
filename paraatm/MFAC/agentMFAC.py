from base import BaseAgent
import numpy as np
import math
# import gym
from collections import namedtuple

import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from torch.distributions import Categorical

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

SavedAction = namedtuple('SavedAction', ['log_prob', 'value', 'baseline_value'])

angle_mode = 24
velocity_mode = 3


class Policy(nn.Module):

    def __init__(self, h, w, outputs, hidden_size, l):
        super(Policy, self).__init__()
        self.conv1 = nn.Conv2d(4, 16, kernel_size=3, stride=1, padding=2)
        self.bn1 = nn.BatchNorm2d(16)
        self.conv2 = nn.Conv2d(16, 32, kernel_size=3, stride=1, padding=2)
        self.bn2 = nn.BatchNorm2d(32)
        self.conv3 = nn.Conv2d(32, 32, kernel_size=3, stride=2, padding=2)
        self.bn3 = nn.BatchNorm2d(32)


        # Number of Linear input connections depends on output of conv2d layers
        # and therefore the input image size, so compute it.
        def conv2d_size_out(size, kernel_size=3, stride=1, padding=2):
            return (size + 2 * padding - kernel_size) // stride + 1
        convw = conv2d_size_out(conv2d_size_out(conv2d_size_out(w)), stride=2)
        convh = conv2d_size_out(conv2d_size_out(conv2d_size_out(h)), stride=2)
        linear_input_size = convw * convh * 32
        # self.head = nn.Linear(linear_input_size, outputs)
        self.hid_linear = nn.Linear(linear_input_size + l, hidden_size)
        self.action_head = nn.Linear(hidden_size, outputs)
        self.value_head = nn.Linear(hidden_size, 1)

        self.saved_actions = []
        self.saved_return = []

    # Called with either one element to determine next action, or a batch
    # during optimization. Returns tensor([[left0exp,right0exp]...]).
    def forward(self, x, s):
        if (x != x).any() or (s != s).any():
            print("Error: NaN")
        x = F.relu(self.bn1(self.conv1(x)))
        x = F.relu(self.bn2(self.conv2(x)))
        x = F.relu(self.bn3(self.conv3(x)))
        test1 = x.view(x.size(0), -1)
        test2 = s
        test3 = torch.cat((x.view(x.size(0), -1), s), 1)
        feature = F.relu(self.hid_linear(torch.cat((x.view(x.size(0), -1), s), 1)))
        action_scores = self.action_head(feature)
        state_values = self.value_head(feature)

        return F.softmax(action_scores, dim=-1), state_values


class MFACAgent(BaseAgent):

    def __init__(self, num_UAV, grid_size):

        """Declare agent variables."""
        self.num_UAV = num_UAV
        self.grid_size = grid_size
        self.alpha = 0.00
        self.gamma = 0.95
        self.epsilon = 0.00
        self.mode = "Train"
        self.action_space = [-2, -1, 0, 1, 2]
        # self.coords = [(-1, 0), (1, 0), (0, 1), (0, -1)]
        # self.returns = dict(zip(self.action_space, self.coords))
        self.view_length = 10

        self.action = None
        self.pos = None
        self.state = None
        self.heading = None
        self.relative_state = None
        self.state_image_list = None
        self.course = None
        self.goal = None
        self.arrived = None
        self.TARGET_UPDATE = 10
        self.BATCH_SIZE = 128
        # self.policy_net = Policy((2 * self.view_length - 1), (2 * self.view_length - 1), len(self.action_space), 50,
        #                          4*self.grid_size-2 + angle_mode ).to(device)
        self.policy_net = Policy((2 * self.view_length - 1), (2 * self.view_length - 1),
                                 len(self.action_space), 50, 4).to(device)
        # self.policy_net.load_state_dict(torch.load('Data/MFQMulti_v3_' + str(self.grid_size) + '_trainedAC0'))
        self.policy_net.eval()
        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=0.001)
        self.action_to_idx = dict(zip(self.action_space, range(len(self.action_space))))
        self.V = None

    def agent_init(self, mode, idx):
        """
        Arguments: Nothing
        Returns: Nothing
        Hint: Initialize the variables that need to be reset before each run
        begins
        Initialize the alpha,epsilon,all actions and Q
        """
        self.mode = mode
        # if self.mode == "Test":
        #     self.policy_net.load_state_dict(
        #         torch.load('Data/MFQMulti_v3_' + str(self.grid_size) + '_trainedAC' + str(idx)))
        # self.V = np.load('Data/MFAC_100_initial_v3nn_V.npy', mmap_mode='c')
        self.policy_net.saved_actions = [[] for j in range(self.num_UAV)]
        self.policy_net.saved_return = [[] for j in range(self.num_UAV)]

    def agent_start(self, pos, state, tas, course, state_image_list, goal, epsilon=0.3, alpha=0.05):
        """
        Arguments: state - numpy array
        Returns: action - integer
        Hint: Initialize the variables that you want to reset before starting
        a new episode, pick the first action, don't forget about exploring
        starts
        """
        # x,y=state
        self.epsilon = epsilon
        self.alpha = alpha
        self.pos = pos
        self.state = state
        self.goal = goal
        self.state_image_list = state_image_list
        self.arrived = [False] * self.num_UAV

        self.action = self._chooseAction(self.state, tas, course, state_image_list)
        # self.policy_net.load_state_dict(torch.load('Data/MFQMulti_' + str(self.grid_size) + '_trained_v2nn'))

        return self.action

    def agent_step(self, reward, pos_new, state_new, tas, course, state_image_list, arrived):
        """
        Arguments: reward - floating point, state - numpy array
        Returns: action - integer
        Hint: select an action based on pi
        """
        for uav in range(self.num_UAV):
            # relative_state_new.append(tuple(map(lambda x, y: (x - y), state_new[uav], self.goal[uav])))
            if arrived[uav] and (not self.arrived[uav]):
                self.arrived[uav] = True
                self.policy_net.saved_return[uav].append(reward[uav])
        # for uav in range(self.num_UAV):
        #     self.policy_net.saved_return[uav].append(reward[uav])

        self.action = self._chooseAction(state_new, tas, course, state_image_list, reward)
        self.state = state_new
        self.pos = pos_new

        return self.action

    def agent_end(self, reward):
        """
        Arguments: reward - floating point
        Returns: Nothing
        Hint: do necessary steps for policy evaluation and improvement
        """
        for uav in range(self.num_UAV):
            if not self.arrived[uav]:
                self.policy_net.saved_return[uav].append(reward[uav])

    def agent_update(self, policy_update=False):
        if policy_update:
            saved_actions_all = []
            policy_losses = []
            value_losses = []
            value_returns = []
            # value_baseline = []
            for uav in range(self.num_UAV):
                while self.policy_net.saved_return[uav]:
                    value_returns.append(self.policy_net.saved_return[uav].pop(0))
                    saved_actions_all.append(self.policy_net.saved_actions[uav].pop(0))
            if value_returns:
                value_returns = torch.tensor(value_returns)
                for (log_prob, value, value_baseline), G in zip(saved_actions_all, value_returns):
                    advantage = G - value.item()
                    policy_losses.append(-log_prob * advantage)
                    value_losses.append(F.smooth_l1_loss(value, torch.tensor([G]).to(device)))
                self.optimizer.zero_grad()
                loss = torch.stack(policy_losses).sum() + torch.stack(value_losses).sum()
                loss.backward()
                self.optimizer.step()
            self.policy_net.saved_actions = [[] for j in range(self.num_UAV)]
            self.policy_net.saved_return = [[] for j in range(self.num_UAV)]

    def agent_message(self, in_message):
        """
        Arguments: in_message - string
        Returns: The value function as a list.
        This function is complete. You do not need to add code here.
        """
        
        pass

    def _chooseAction(self, state, tas, course, state_image_list, reward=None):
        """
        :param relative_state: relative positions of the UAVs compared to corresponding destinations;
                tuple(tuple(x, y) * numUAV)
        :param view: the view of each UAV; tuple(observations * numUAV)
        :return: actions, tuple(string * num_UAV); coord, tuple( tuple(0or1, 0or1) * num_UAV)
        """
        action = []
        coord = []
        for uav in range(len(state)):
            if state[uav] is None:
                action.append(None)
                continue

            # pos_x = np.zeros(2*self.grid_size-1)
            # pos_y = np.zeros(2*self.grid_size-1)
            # heading = np.zeros(angle_mode)
            # v = np.zeros(velocity_mode)
            #
            # # binary_code = np.zeros((2, 2*self.grid_size-1), dtype='f')
            # pos_x[state[uav][0]] = 1
            # pos_y[state[uav][1]] = 1
            # heading[course[uav]] = 1
            # # binary_code = np.append(pos_x, pos_y, heading)
            # binary_code = np.concatenate((pos_x, pos_y, heading))
            # binary_code = binary_code.reshape((1, -1))
            # state_input = np.array(list(binary_code), dtype='f')
            # state_input = torch.from_numpy(state_input)

            pos_x = self.state[uav][0]/10
            pos_y = self.state[uav][0]/10
            ac_course = course[uav]/(2*math.pi)
            ac_tas = tas[uav]/100

            # binary_code = np.zeros((2, 2*self.grid_size-1), dtype='f')
            state_input = np.array([pos_x, pos_y, ac_course, ac_tas], dtype='f')
            state_input = state_input.reshape((1,-1))
            state_input = torch.from_numpy(state_input)

            probs, state_value = self.policy_net(state_image_list[uav].unsqueeze(0).to(device),
                                                 state_input.to(device))

            if self.mode == "Train":
                m = Categorical(probs)
                ac_action = m.sample()
                if not self.arrived[uav]:
                    self.policy_net.saved_actions[uav].append(
                        SavedAction(m.log_prob(ac_action), state_value, 0))
                # self.policy_net.saved_actions[uav].append(
                #     SavedAction(m.log_prob(uav_action), state_value, self.V[relative_state[uav]]))
                if (reward is not None) and (not self.arrived[uav]):
                    self.policy_net.saved_return[uav].append(reward[uav]+self.gamma*state_value)
                # self.policy_net.saved_actions[uav].append(SavedAction(m.log_prob(uav_action), state_value, self.V[relative_state[uav]]))

            else:
                _, ac_action = torch.max(probs, 1)
            action.append(self.action_space[ac_action.item()])

        action = tuple(action)

        return action

    def agent_save(self, idx):
        # with open('Data/MFM_'+ str(self.idx) +'_trained.pkl', 'wb') as f:
        #     pickle.dump(self.M, f, pickle.HIGHEST_PROTOCOL)
        torch.save(self.policy_net.state_dict(), 'sample_data/MFAC_PARAATM_SFO_PHX_trainedAC' + str(idx))


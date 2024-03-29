import os
import numpy as np
from rl_MFAC import RL_MFAC
from envParaATM import ParaATMEnv
from agentMFAC import MFACAgent
import pygame
import matplotlib.pyplot as plt

cur_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(cur_dir, '../sample_data/')

def run(numAC):
    space_size = 30
    dt = 60
    surface = create_window(space_size)
    cfg = {'fp_file': data_dir + 'midair_collision.trx',  # flight plan file
           'mfl_file': data_dir + 'midair_collision_mfl.trx',  # mfl file
           'numAC': numAC,  # text command
           # 'agent_obj': agent,
           'surface_obj': surface,
           'space_size': space_size,
           'dt': dt,
           'sim_time': 200*dt+1000}  # total simulation time
    maxEpisodes = 50000
    # environment = ParaATMEnv(num_UAV, cfg)
    # environment.get_start_info()

    rlglue = RL_MFAC(numAC, space_size, cfg)

    # np.random.seed(1)

    # Train Process
    rlglue.rl_init(0)
    for i in range(maxEpisodes):
        print("Round:", i)
        rlglue.rl_episode()
        print("Steps took in this episode was %d" % (rlglue.num_ep_steps()))
        print("Total cost in this episode was %.2f" % (-rlglue.total_reward()))


def create_window(grid_size):
    title = "Collision Avoidance"
    size = (20 * grid_size, 20 * grid_size)
    pygame.init()
    surface = pygame.display.set_mode(size, 0, 0)
    pygame.display.set_caption(title)

    return surface


if __name__ == "__main__":
    run(2)
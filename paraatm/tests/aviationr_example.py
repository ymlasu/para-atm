import os
import torch
import numpy as np
import pandas as pd
from paraatm.simulation_method.aviationr import AviationRisk
import matplotlib.pyplot as plt
cur_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(cur_dir, '..', 'sample_data/')

cfg = {'fp_file': data_dir + 'aviationR/data/TRX_DEMO_SFO_PHX_GateToGate.trx',  # flight plan file
       'mfl_file': data_dir + 'aviationR/data/TRX_DEMO_SFO_PHX_mfl.trx',  # mfl file
       'data_file': data_dir + 'aviationR/data/', # required data for accident simulation and risk estimation
       'model_file': data_dir + 'aviationR/model/', # Pre-trained model
       'sim_time': 12000}  # total simulation time

# call
sim = AviationRisk(cfg)
device = torch.device('cpu')
if torch.cuda.is_available():
    device = torch.device('cuda')
result  = sim.simulation(device)  # call simulation function using NatsSimulationWrapper

track = pd.read_table(data_dir + 'aviationR/data/trajectory.csv', sep=',', skiprows=[0,1,2,3,4,6,7,8,9], index_col=0)

fig, ax = plt.subplots(3, 1,figsize=(15,30))
x = result['event']
y = np.mean(result['risk'],1)
e = np.var(result['risk'],1)
(_, caps, _) = ax[0].errorbar(
    x, y, e, fmt='--o', ecolor='g', capsize=5, elinewidth=1)
ax[0].set_xticklabels(x, rotation=70)

for cap in caps:
    cap.set_markeredgewidth(1)

tim = np.array(track.index)
lat = track['latitude']
lon = track['longitude']
alt = track['altitude_ft']

ax[1].plot(tim, alt)
for i in result['time']:
    ax[1].plot(i,track.loc[i,'altitude_ft'], color='red', marker='o')
ax[2].plot(lon, lat)
for i in result['time']:
    ax[2].plot(track.loc[i,'longitude'],track.loc[i,'latitude'], color='red', marker='o')
plt.show()
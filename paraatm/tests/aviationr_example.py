import os
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
       'sim_time': 8000}  # total simulation time

# call
sim = AviationRisk(cfg)

nats_sim = sim()
result = nats_sim['sim_results']
track = nats_sim['trajectory']
if result is not None:

    fig, ax = plt.subplots(1, 3,figsize=(12,4))
    x = result['event']
    y = np.mean(result['risk'],1)
    e = np.var(result['risk'],1)
    (_, caps, _) = ax[0].errorbar(
        x, y, e, fmt='--o', ecolor='g', capsize=5, elinewidth=1)
    ax[0].set_xticklabels(x, rotation=20)

    for cap in caps:
        cap.set_markeredgewidth(1)

    tim = track.time.values.astype(np.float)
    lat = track['latitude']
    lon = track['longitude']
    alt = track['altitude']

    ax[1].plot(tim, alt)
    for i in result['time']:
        ax[1].plot(tim[i],alt[i], color='red', marker='o')
    ax[2].plot(lon, lat)
    for i in result['time']:
        ax[2].plot(lon[i],lat[i], color='red', marker='o')
    plt.show()
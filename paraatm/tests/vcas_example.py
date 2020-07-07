#from vcasmodule import VCAS
import os
import numpy as np
from paraatm.plotting import plot_trajectory
from paraatm.simulation_method.vcas import VCAS
import matplotlib.pyplot as plt

cur_dir = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(cur_dir, '..', 'sample_data/')
# user need to set environmental variable NATS_HOME
# input for VCAS
cfg = {'fp_file': data_dir + 'vcas/ASU123at6000.trx',  # flight plan file
       'mfl_file': data_dir + 'vcas/ASU123_mfl.trx',  # mfl file
       'cmd_file': data_dir + 'vcas/command.csv',  # text command
       'data_file': data_dir + 'vcas/ASU123.csv',  # actual trajectory data
       'sim_time': 1000}  # total simulation time

# call
sim = VCAS(cfg)

track = sim()['trajectory']  # call simulation function using NatsSimulationWrapper

# plot_trajectory(track)  # plot using bokeh method

real = sim.real
com = sim.command_from_file()

tim = track.time.values.astype(np.float) // 1e9
lat = track['latitude']
lon = track['longitude']
alt = track['altitude']
fig, ax = plt.subplots(1, 2)
ax[0].plot(tim, alt)
ax[0].plot(real['timestamp'].values, 100 * real['altitude'].values)
ax[0].plot(com['Timestamp'].values, com['altitude'].values, 'o')
ax[0].set_ylim(0, 6000)
ax[0].set_xlim(sim.starttime, sim.starttime + sim.sim_time)

ax[1].plot(lon, lat)
ax[1].plot(real['longitude'].values, real['latitude'].values)
ax[1].plot(sim.fp_lon, sim.fp_lat, 'o')
ax[1].set_xlim(-85.0, -84.4)
ax[1].set_ylim(33.3, 33.7)
plt.show()

post = sim.model_update()
fig2 = plt.figure()
ax2 = fig2.add_subplot(1, 1, 1)
for p in post:
    ax2.plot(p[:, 0], p[:, 1])
ax2.set_ylim(0, 1.1)
plt.show()


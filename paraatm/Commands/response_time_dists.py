import numpy as np
import pandas as pd
from scipy.stats import norm,lognorm
import matplotlib.pyplot as plt

Nsamps = 1000
# Pilot Response Times
pilot_rt_nom = lognorm(0.1,0.25)
pilot_rt_off = lognorm(0.2,0.5)

#ATCo Response Times
atco_rt_nom = lognorm(0.2,0.5)
atco_rt_off = lognorm(0.4,0.75)

#Vehicle Response Times
veh_rt_nom = lognorm(0.5,1.5)
veh_rt_off = lognorm(1.0,2.0)

nom_dists = [pilot_rt_nom,atco_rt_nom,veh_rt_nom]
off_dists = [pilot_rt_off,atco_rt_off,veh_rt_off]

rv_nom = np.array([rv.rvs(size=Nsamps) for rv in nom_dists]).T
rv_off = np.array([rv.rvs(size=Nsamps) for rv in off_dists]).T

total_rt_nom = np.sum(rv_nom,axis=0)
total_rt_off =  np.sum(rv_off,axis=0)

labels = ['Pilot','ATCo','Vehicle']

fig = plt.figure(figsize=np.array([4,3]))
ax = fig.gca()
for i,rv in enumerate(nom_dists):
    x = np.linspace(rv.ppf(0.0001),rv.ppf(0.999),100000)
    ax.plot(x,rv.pdf(x),label=labels[i])
    ax.set_ylim(bottom=0)
    ax.set_xlim([0,10])
    ax.set_xlabel('Time, s')
    ax.set_ylabel('PDF')

plt.title('Nominal Response Times')
plt.legend(loc=1)
plt.show()

plt.savefig('figures/Nominal_response_times.png',bbox_inches='tight')

fig = plt.figure(figsize=np.array([4,3]))
ax = fig.gca()
for i,rv in enumerate(off_dists):
    x = np.linspace(rv.ppf(0.0001),rv.ppf(0.998),100000)
    ax.plot(x,rv.pdf(x),label=labels[i])
    ax.set_ylim(bottom=0)
    ax.set_xlim([0,10])
    ax.set_xlabel('Time, s')
    ax.set_ylabel('PDF')

plt.title('Off-Nominal Response Times')
plt.legend(loc=1)
plt.show()

plt.savefig('figures/Off-nominal_response_times.png',bbox_inches='tight')


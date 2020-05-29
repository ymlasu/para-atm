"""
NASA University Leadership Initiative program
Information fusion for real-time national air transportation system prognostics under uncertainty

    Real-time flight health monitoring uisng autoencoder (AE)
    - From KSFO to KPHX during cruise to approach operation
    - Generate normal & upset flight scenarios
    - Flight health monitoring & upset detection

    @author: Hyunseong Lee, Adaptive Intelligent Materials & Systems (AIMS) Center,
             Arizona State University
    
    Last modified on 5/25/2020
"""

# Locate PARA_ATM Home directory
import os
os.chdir("/home/hector/Documents/para-atm-master")

from paraatm.io.gnats import read_gnats_output_file
from paraatm.simulation_method.integrated_flight_health_monitoring import IFHM
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Set GNATS_Home and data directories
os.environ["GNATS_Home"] = "/home/hector/Documents/GNATS"
dir_data = "/home/hector/Documents/para-atm-master/paraatm/sample_data/"
os.environ["dir_data"] = dir_data
os.environ["out_path"] = dir_data

#%% Upset case 1: rudder upset

# Setup simulation with IFHM
# alt_rate_coef [ft], tas_rate_coef [knots], course_rate_coef [deg]
sim_inputs1 = {"fp_file": dir_data + "TRX_KSFO_KPHX_mid_approach.trx",
                "mfl_file": dir_data + "TRX_KSFO_KPHX_mfl.trx",
                "cruz_alt": 32000,
                "upset_case": 1,
                "upset_init": 1100,
                "upset_dur": 180,
                "alt_rate_coef": 0.15,
                "tas_rate_coef": 0.005,
                "course_rate_coef": 0.002,
                "th_Mahal_dist": 18}

sim1 = IFHM(sim_inputs1)
sim1.setup_fhm()

# Run normal case simulation
norm_out_fname = sim1.simulation_normal()
# Save output
sim1.write_output(norm_out_fname)
# Read output
norm_out = read_gnats_output_file(norm_out_fname)

# Run upset case simulation
upset_out_fname, org_feats, sc_feats, rec_feats, sc_rec_feats, rec_errors, Mahal_dists, upset_metrics = sim1.simulation_upset()
# Save output
sim1.write_output(upset_out_fname)
# Read output
upset_out = read_gnats_output_file(upset_out_fname)

# Compare normal vs upset
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(norm_out.longitude, norm_out.latitude, norm_out.altitude, c='blue', label='Normal')
ax.plot(upset_out.longitude, upset_out.latitude, upset_out.altitude, c='red', label='Upset')
ax.set_xlabel('Longitude [deg]')
ax.set_ylabel('Latitude [deg]')
ax.set_zlabel('Altitude [ft]')
ax.legend()

plt.figure()
plt.subplot(311)
plt.plot(norm_out.rocd, c='blue', label='Normal')
plt.plot(upset_out.rocd, c='red', label='Upset')
plt.ylabel('ROCD [ft/s]'); plt.legend()
plt.subplot(312)
plt.plot(norm_out.tas, c='blue', label='Normal')
plt.plot(upset_out.tas, c='red', label='Upset')
plt.ylabel('TAS [knots]'); plt.legend()
plt.subplot(313)
plt.plot(norm_out.heading, c='blue', label='Normal')
plt.plot(upset_out.heading, c='red', label='Upset')
plt.xlabel('Time [s]'); plt.ylabel('Heading [deg]'); plt.legend()


# Compare upset original and reconstruction with detection
pind = np.arange(1,1280)
det_ind = np.where(upset_metrics == 1)[0]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(upset_out.longitude[pind], upset_out.latitude[pind], upset_out.altitude[pind], c='black', label='Org')
ax.plot(rec_feats[:,1], rec_feats[:,0], rec_feats[:,2], c='blue', label='Reconst')
ax.plot(rec_feats[det_ind,1], rec_feats[det_ind,0], rec_feats[det_ind,2], 'o', c='red', label='Detect')
ax.set_xlabel('Longitude [deg]')
ax.set_ylabel('Latitude [deg]')
ax.set_zlabel('Altitude [ft]')
ax.legend()

plt.figure()
plt.subplot(311)
plt.plot(upset_out.rocd[pind], c='black', label='Org')
plt.plot(rec_feats[:,3], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,3], 'o', c='red', label='Detect')
plt.ylabel('ROCD [ft/s]'); plt.legend()
plt.subplot(312)
plt.plot(upset_out.tas[pind], c='black', label='Org')
plt.plot(rec_feats[:,4], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,4], 'o', c='red', label='Detect')
plt.ylabel('TAS [knots]'); plt.legend()
plt.subplot(313)
plt.plot(upset_out.heading[pind], c='black', label='Org')
plt.plot(rec_feats[:,5], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,5], 'o', c='red', label='Detect')
plt.xlabel('Time [s]'); plt.ylabel('Heading [deg]'); plt.legend()

plt.figure();
plt.plot(Mahal_dists, c='blue', label='Mahal_dist')
plt.plot(det_ind, Mahal_dists[det_ind], 'o', c='red', label='Detect')
plt.xlabel('Time [s]'); plt.ylabel('Mahalanobis distance'); plt.legend()


#%% Upset case 2: left aileron upset; spiral-dive

sim_inputs2 = {"fp_file": dir_data + "TRX_KSFO_KPHX_mid_approach.trx",
                "mfl_file": dir_data + "TRX_KSFO_KPHX_mfl.trx",
                "cruz_alt": 32000,
                "upset_case": 2,
                "upset_init": 1100,
                "upset_dur": 180,
                "alt_rate_coef": 0.15,
                "tas_rate_coef": 0.002,
                "course_rate_coef": 7,
                "th_Mahal_dist": 20}

sim2 = IFHM(sim_inputs2)
sim2.setup_fhm()

# Run normal case simulation
norm_out_fname = sim2.simulation_normal()
# Save output
sim2.write_output(norm_out_fname)
# Read output
norm_out = read_gnats_output_file(norm_out_fname)

# Run upset case simulation
upset_out_fname, org_feats, sc_feats, rec_feats, sc_rec_feats, rec_errors, Mahal_dists, upset_metrics = sim2.simulation_upset()
# Save output
sim2.write_output(upset_out_fname)
# Read output
upset_out = read_gnats_output_file(upset_out_fname)

# Compare normal vs upset
fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(norm_out.longitude, norm_out.latitude, norm_out.altitude, c='blue', label='Normal')
ax.plot(upset_out.longitude, upset_out.latitude, upset_out.altitude, c='red', label='Upset')
ax.set_xlabel('Longitude [deg]')
ax.set_ylabel('Latitude [deg]')
ax.set_zlabel('Altitude [ft]')
ax.legend()

plt.figure()
plt.subplot(311)
plt.plot(norm_out.rocd, c='blue', label='Normal')
plt.plot(upset_out.rocd, c='red', label='Upset')
plt.ylabel('ROCD [ft/s]'); plt.legend()
plt.subplot(312)
plt.plot(norm_out.tas, c='blue', label='Normal')
plt.plot(upset_out.tas, c='red', label='Upset')
plt.ylabel('TAS [knots]'); plt.legend()
plt.subplot(313)
plt.plot(norm_out.heading, c='blue', label='Normal')
plt.plot(upset_out.heading, c='red', label='Upset')
plt.xlabel('Time [s]'); plt.ylabel('Heading [deg]'); plt.legend()


# Compare upset original and reconstruction with detection
pind = np.arange(1,1280)
det_ind = np.where(upset_metrics == 1)[0]

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(upset_out.longitude[pind], upset_out.latitude[pind], upset_out.altitude[pind], c='black', label='Org')
ax.plot(rec_feats[:,1], rec_feats[:,0], rec_feats[:,2], c='blue', label='Reconst')
ax.plot(rec_feats[det_ind,1], rec_feats[det_ind,0], rec_feats[det_ind,2], 'o', c='red', label='Detect')
ax.set_xlabel('Longitude [deg]')
ax.set_ylabel('Latitude [deg]')
ax.set_zlabel('Altitude [ft]')
ax.legend()

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.plot(upset_out.longitude[pind], upset_out.latitude[pind], upset_out.altitude[pind], c='black', label='Org')
ax.plot(upset_out.longitude[det_ind+1], upset_out.latitude[det_ind+1], upset_out.altitude[det_ind+1], 'o', c='red', label='Detect')
ax.set_xlabel('Longitude [deg]')
ax.set_ylabel('Latitude [deg]')
ax.set_zlabel('Altitude [ft]')
ax.legend()

plt.figure()
plt.subplot(311)
plt.plot(upset_out.rocd[pind], c='black', label='Org')
plt.plot(rec_feats[:,3], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,3], 'o', c='red', label='Detect')
plt.ylabel('ROCD [ft/s]'); plt.legend()
plt.subplot(312)
plt.plot(upset_out.tas[pind], c='black', label='Org')
plt.plot(rec_feats[:,4], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,4], 'o', c='red', label='Detect')
plt.ylabel('TAS [knots]'); plt.legend()
plt.subplot(313)
plt.plot(upset_out.heading[pind], c='black', label='Org')
plt.plot(rec_feats[:,5], c='blue', label='Reconst')
plt.plot(det_ind, rec_feats[det_ind,5], 'o', c='red', label='Detect')
plt.xlabel('Time [s]'); plt.ylabel('Heading [deg]'); plt.legend()

plt.figure();
plt.plot(Mahal_dists, c='blue', label='Mahal_dist')
plt.plot(det_ind, Mahal_dists[det_ind], 'o', c='red', label='Detect')
plt.xlabel('Time [s]'); plt.ylabel('Mahalanobis distance'); plt.legend()
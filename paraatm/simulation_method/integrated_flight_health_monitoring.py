"""
NASA University Leadership Initiative program
Information fusion for real-time national air transportation system prognostics under uncertainty

    Integrated Flight Heatlrh Monitoring (IFHM) module
    - Simulate normal flight operation
    - Simulate flight with upset flight scenarios using 1) upgen sub module
    - Monitor flight health in real-time and detect aircraft upsets
      using 2) fhm sub module
    - Generate output files to perform analysis

    @author: Hyunseong Lee, Adaptive Intelligent Materials & Systems (AIMS) Center,
             Arizona State University
    
    Last modified on 5/25/2020
"""

import time
import os
from jpype import *
from array import *
from shutil import copyfile
from scipy import signal
import numpy as np
import math
import pandas as pd
import tensorflow as tf
from tensorflow.keras import backend
from tensorflow.keras.models import Model, load_model
from tensorflow.keras.layers import Input, Dense, BatchNormalization
from tensorflow.keras.regularizers import l1
from tensorflow.keras import optimizers
from paraatm.io.gnats import GnatsSimulationWrapper
from paraatm.simulation_method.upset_gen import upgen
from paraatm.simulation_method.flight_health_monitor import fhm

class IFHM(GnatsSimulationWrapper):
    def __init__(self, sim_inputs):
        
        # GNATS simulation input files
        self.fp_file = sim_inputs["fp_file"]
        self.mfl_file = sim_inputs["mfl_file"]
        self.cruz_alt = sim_inputs["cruz_alt"]
        self.upset_case = sim_inputs["upset_case"]
        self.upset_init = sim_inputs["upset_init"]
        self.upset_dur = sim_inputs["upset_dur"]
        self.alt_rate_coef = sim_inputs["alt_rate_coef"]
        self.tas_rate_coef = sim_inputs["tas_rate_coef"]
        self.course_rate_coef = sim_inputs["course_rate_coef"]
        self.th_Mahal_dist = sim_inputs["th_Mahal_dist"]
        
        # Define GNATS-Server environment (not standalone) & perform simulation
        # Set PARA-ATM & GNATS folders
        # PARA_ATM_Home = os.environ.get('PARA_ATM_Home')
        GNATS_Home = os.environ.get("GNATS_Home")
        GNATS_Client = GNATS_Home + "/GNATS_Client"
        GNATS_Server = GNATS_Home + "/GNATS_Server"
        
        # Locate working directory to GNATS Client folder
        os.chdir(GNATS_Client)
        
        # Set classpath & start JVM (GNATS-Server)
        classpath = "dist/gnats-client.jar:dist/gnats-shared.jar:dist/json.jar:dist/rmiio-2.1.2.jar:dist/commons-logging-1.2.jar"
        startJVM(getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % classpath)

        # NATS simulation status definition
        self.GNATS_SIMULATION_STATUS_READY = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_READY
        self.GNATS_SIMULATION_STATUS_START = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_START
        self.GNATS_SIMULATION_STATUS_PAUSE = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_PAUSE
        self.GNATS_SIMULATION_STATUS_RESUME = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_RESUME
        self.GNATS_SIMULATION_STATUS_STOP = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_STOP
        self.GNATS_SIMULATION_STATUS_ENDED = JPackage('com').osi.util.Constants.GNATS_SIMULATION_STATUS_ENDED
    
        GNATSClientFactory = JClass('GNATSClientFactory')
        GnatsClient = GNATSClientFactory.getGNATSClient()
        
        # Define interfaces
        self.simulationInterface = GnatsClient.getSimulationInterface()
        self.equipmentInterface = GnatsClient.getEquipmentInterface()
        self.aircraftInterface = self.equipmentInterface.getAircraftInterface()
        self.entityInterface = GnatsClient.getEntityInterface()
        self.pilotInterface = self.entityInterface.getPilotInterface()
        self.groundOperatorInterface = self.entityInterface.getGroundOperatorInterface()
        self.groundVehicleInterface = self.equipmentInterface.getGroundVehicleInterface()
        self.controllerInterface = self.entityInterface.getControllerInterface()
        self.cnsInterface = self.equipmentInterface.getCNSInterface()
        self.environmentInterface = GnatsClient.getEnvironmentInterface()
        self.airportInterface = self.environmentInterface.getAirportInterface()
        self.terminalAreaInterface = self.environmentInterface.getTerminalAreaInterface()
        self.weatherInterface = self.environmentInterface.getWeatherInterface()
        self.safetyMetricsInterface = GnatsClient.getSafetyMetricsInterface()
        self.terrainInterface = self.environmentInterface.getTerrainInterface()
        
        # Set wind info file folder path
        self.dir_share = GNATS_Server + "/share"
        
        # Set output file folder path
        self.out_path = os.environ.get("out_path")
        
        if (GnatsClient is None) :
        	print("Can't start GNATS Client")
        	quit()
    
    
    def setup_fhm(self):
        
        # Set data directory
        dir_data = os.environ.get("dir_data")
        
        # Load values for scaling features
        scale_fname = "scale_cnst_crz_aprch_28-34k.csv"
        scale_cnst = pd.read_csv(dir_data + scale_fname)
        self.df = scale_cnst.loc[scale_cnst.cruz_alt == self.cruz_alt].values.flatten()
        
        # Load trained AE model for health monitoring (AE_GNATS)
        AE_fname = "AE_KSFO_KPHX_cruz_aprch.h5"
        self.AE_GNATS = load_model(dir_data + AE_fname)
        
        # Load mean and covariance matrix file to calculate Mahalanobis distance
        mean_cov_fname = "error_mean_cov_crz_aprch_28-34k.csv"
        mean_cov = pd.read_csv(dir_data + mean_cov_fname, header=None)
        self.mean = np.array(mean_cov.iloc[0,1:9])
        self.cov = np.array(mean_cov.iloc[1:9,1:9])
        self.cov_inverse = np.linalg.inv(self.cov)
        

    def simulation_normal(self, *args, **kwargs):
        self.simulationInterface.clear_trajectory()
        self.environmentInterface.load_rap(self.dir_share + "/tg/rap")
        self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)
        
        T_total = self.upset_init + self.upset_dur # Total simulation time
        T_step = 1 # Simulation time step & pause time step
        self.simulationInterface.setupSimulation(T_total, T_step)
        self.simulationInterface.start()
        # self.simulationInterface.start(T_step) #*** Pause-resume simulation in each T_step *** 1/2
                
        while True:
            runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == self.GNATS_SIMULATION_STATUS_PAUSE):
                
                # Show current simulation time
                curr_sim_time = self.simulationInterface.get_curr_sim_time()
                print("Current sim time: %d" %curr_sim_time)
                # self.simulationInterface.resume(T_step) #*** Pause-resume simulation in each T_step *** 2/2
                
            elif (runtime_sim_status == self.GNATS_SIMULATION_STATUS_ENDED):
                break                       
            else:
                time.sleep(1)
        
        # Set output file name
        save_time = time.strftime('%Y-%m%d-%H%M')
        normal_out_fname = self.out_path + "/normal_crz_aprch_" + save_time + ".csv"       
        return normal_out_fname
                
        # Disconnect with NATS Server  
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()
        # gnatsClient.disConnect()


    def simulation_upset(self, *args, **kwargs):
        self.simulationInterface.clear_trajectory()
        self.environmentInterface.load_rap(self.dir_share + "/tg/rap")
        self.aircraftInterface.load_aircraft(self.fp_file, self.mfl_file)
        
        T_total = self.upset_init + self.upset_dur # Total simulation time
        T_step = 1 # Simulation time step & pause time step
        self.simulationInterface.setupSimulation(T_total, T_step)
        self.simulationInterface.start(T_step) #*** Pause-resume simulation in each T_step *** 1/2
        
        ctr = 0
        temp1 = []; temp2 = []; temp3 = []; temp4 = []; temp5 = []; temp6 = []
        while True:
            runtime_sim_status = self.simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == self.GNATS_SIMULATION_STATUS_PAUSE):
                
                "-------- Set new state aircraft value in each time step --------"
                # Show current simulation time
                curr_sim_time = self.simulationInterface.get_curr_sim_time()
                print("Current sim time: %d" %curr_sim_time)
                
                # Set Aircraft
                ac0 = self.aircraftInterface.select_aircraft(self.aircraftInterface.getAllAircraftId()[0])
                
                # Upset initiation
                if curr_sim_time == self.upset_init-1:
                    
                    alt_in = ac0.getAltitude_ft()
                    tas_in = ac0.getTas_knots()
                    course_in = ac0.getCourse_rad() * 180/3.1415926 # in degress
                    duration = self.upset_dur
                    
                    # Define upset generation function
                    upsetgen_func = upgen(alt_in, self.alt_rate_coef, tas_in, self.tas_rate_coef, course_in, self.course_rate_coef, self.upset_dur)
                    
                    # Case 1: rudder upset
                    if self.upset_case == 1:
                        alt_post, tas_post, course_post = upsetgen_func.rudder_upset()
                    
                    # Case 2: left aileron upset; spiral-dive
                    elif self.upset_case == 2:
                        alt_post, tas_post, course_post = upsetgen_func.aileron_upset()
                
                if curr_sim_time == self.upset_init:
                    print("Upset initiation at %d sec" %curr_sim_time)
                
                # Set upset aircraft variables
                if curr_sim_time >= self.upset_init:
                    ac0.setAltitude_ft(alt_post[ctr])
                    ac0.setTas_knots(tas_post[ctr])
                    ac0.setCourse_rad(course_post[ctr]*3.1415926/180)
                    ctr = ctr + 1
                    print("Upset sim time: %d s" %ctr) 
                
                # Get aircraft variables
                lat = ac0.getLatitude_deg()
                long = ac0.getLongitude_deg()
                alt = ac0.getAltitude_ft()
                rocd = ac0.getRocd_fps()
                tas = ac0.getTas_knots()
                course_deg = ac0.getCourse_rad() * 180/3.1415926 # in degree
                fpa = ac0.getFpa_rad() * 180/3.1415926 # in degree
                ph = ac0.getFlight_phase()
                
                # Original features
                org_feat = np.asmatrix([lat, long, alt, rocd, tas, course_deg, fpa, ph])
                temp1.append(org_feat)
                
                # Scale features
                sc_lat = (lat - self.df[1])/(self.df[2]-self.df[1])
                sc_long = (long - self.df[3])/(self.df[4]-self.df[3])
                sc_alt = (alt - self.df[5])/(self.df[6]-self.df[5])
                sc_rocd = (rocd - self.df[7])/(self.df[8]-self.df[7])
                sc_tas = (tas - self.df[9])/(self.df[10]-self.df[9])
                sc_course = (course_deg - self.df[11])/(self.df[12]-self.df[11])
                sc_fpa = (fpa - self.df[13])/(self.df[14]-self.df[13])
                sc_ph = (ph - self.df[15])/(self.df[16]-self.df[15])
                sc_feat = np.asmatrix([sc_lat, sc_long, sc_alt, sc_rocd, sc_tas, sc_course, sc_fpa, sc_ph])
                temp2.append(sc_feat)
                             
                # Reconstruct features using AE_GNATS
                rec_feat = self.AE_GNATS.predict(sc_feat)
                temp3.append(rec_feat)
                
                # Caculate reconstruction errors
                rec_error = sc_feat - rec_feat
                temp4.append(rec_error)
                
                # Evaluate upset metric to monitor aircraft system health
                fhm_func = fhm(rec_error, self.mean, self.cov, self.cov_inverse, self.th_Mahal_dist)
                Mahal_dist, upset_metric = fhm_func.rt_fhm()
                temp5.append(Mahal_dist)
                temp6.append(upset_metric)
                
                print("[alt, tas, course, ph] = %.2f, %.2f, %.2f, %d" %(alt, tas, course_deg, ph))
                print('\n')
                self.simulationInterface.resume(T_step) #*** Pause-resume simulation in each T_step *** 2/2
        
            elif (runtime_sim_status == self.GNATS_SIMULATION_STATUS_ENDED):
                break                       
                
            else:
                time.sleep(1)
        
        # Save variables
        org_feats = np.vstack(temp1)
        sc_feats = np.vstack(temp2)
        sc_rec_feats = np.vstack(temp3)
        
        rec_feats = np.empty(sc_rec_feats.shape)
        for j in range(0,8):
            rec_feats[:,j] = sc_rec_feats[:,j] * (self.df[2*(j+1)] - self.df[2*j+1]) + self.df[2*j+1]
        
        rec_errors = np.vstack(temp4)
        Mahal_dists = np.vstack(temp5)
        upset_metrics = np.vstack(temp6)
        
        # Set output file name
        save_time = time.strftime('%Y-%m%d-%H%M')
        upset_out_fname = self.out_path + "/upset_crz_aprch_" + save_time + ".csv"
        
        return upset_out_fname, org_feats, sc_feats, rec_feats, sc_rec_feats, rec_errors, Mahal_dists, upset_metrics
         
        # Close connection from NATS Server  
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()
        # gnatsClient.disConnect()

        
    def write_output(self, filename):
        
        # Save output
        print("Saving GNATS simulation output data.  Please wait....")
        self.simulationInterface.write_trajectories(filename)
        
        
    def cleanup(self):
        
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()
import time

from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment

class GateToGate(NatsSimulationWrapper):
    def simulation(self):

        NATS_SIMULATION_STATUS_PAUSE = NatsEnvironment.get_nats_constant('GNATS_SIMULATION_STATUS_PAUSE')
        NATS_SIMULATION_STATUS_ENDED = NatsEnvironment.get_nats_constant('GNATS_SIMULATION_STATUS_ENDED')

        DIR_share = NatsEnvironment.share_dir
        
        natsStandalone = NatsEnvironment.get_nats_standalone()

        simulationInterface = natsStandalone.getSimulationInterface()

        entityInterface = natsStandalone.getEntityInterface()
        controllerInterface = entityInterface.getControllerInterface()
        pilotInterface = entityInterface.getPilotInterface()

        environmentInterface = natsStandalone.getEnvironmentInterface()

        equipmentInterface = natsStandalone.getEquipmentInterface()
        aircraftInterface = equipmentInterface.getAircraftInterface()

        if simulationInterface is None:
            natsStandalone.stop()
            raise RuntimeError("Can't get SimulationInterface")
        
        simulationInterface.clear_trajectory()

        environmentInterface.load_rap(DIR_share + "/tg/rap")

        aircraftInterface.load_aircraft(DIR_share + "/tg/trx/TRX_DEMO_SFO_PHX_GateToGate.trx", DIR_share + "/tg/trx/TRX_DEMO_SFO_PHX_mfl.trx")

    #     # Controller to set human error: delay time
    #     # Users can try the following setting and see the difference in trajectory
        #controllerInterface.setDelayPeriod("SWA1897", AIRCRAFT_CLEARANCE_PUSHBACK, 7)
        #controllerInterface.setDelayPeriod("SWA1897", AIRCRAFT_CLEARANCE_TAKEOFF, 20)

        simulationInterface.setupSimulation(12000, 30) # SFO - PHX

        simulationInterface.start(660)

        # Use a while loop to constantly check simulation status.  When the simulation finishes, continue to output the trajectory data
        while True:
            runtime_sim_status = simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == NATS_SIMULATION_STATUS_PAUSE) :
                break
            else:
                time.sleep(1)

        # Pilot to set error scenarios
        # Users can try the following setting and see the difference in trajectory
        #pilotInterface.skipFlightPhase('SWA1897', 'FLIGHT_PHASE_CLIMB_TO_CRUISE_ALTITUDE')
        #pilotInterface.setActionRepeat('SWA1897', "VERTICAL_SPEED")
        #pilotInterface.setWrongAction('SWA1897', "AIRSPEED", "FLIGHT_LEVEL")
        #pilotInterface.setActionReversal('SWA1897', 'VERTICAL_SPEED')
        #pilotInterface.setPartialAction('SWA1897', 'COURSE', 200, 50)
        #pilotInterface.skipChangeAction('SWA1897', 'COURSE')
        #pilotInterface.setActionLag('SWA1897', 'COURSE', 10, 0.05, 60)

        simulationInterface.resume()

        while True:
            runtime_sim_status = simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == NATS_SIMULATION_STATUS_ENDED) :
                break
            else:
                time.sleep(1)

        # Store attribute for access by write_output and cleanup:
        self.simulationInterface = simulationInterface
        self.environmentInterface = environmentInterface
        self.aircraftInterface = aircraftInterface

    def write_output(self, filename):
        self.simulationInterface.write_trajectories(filename)

    def cleanup(self):
        self.aircraftInterface.release_aircraft()
        self.environmentInterface.release_rap()        

"""Functions for interfacing to GNATS simulation"""

import pandas as pd
import numpy as np
from io import StringIO
import os
import jpype
import tempfile
import atexit
import time


# Note: GnatsEnvironment is implemented as a class wtih static methods.
# The same effect could be achieved using globally defined functions
# and state variables, but the class is used in order to provide some
# organization and encapuslation.
#
# Implementation of these utilities was challenging because the JVM
# and GNATS servers can only be started once.  After they are stopped,
# they cannot be started again within the same Python process.  This
# is why we need global (static) variables to track the state and trap
# conditions that would otherwise lead to crashes.
#
# Other approaches that were considered: Use of a context manager
# class was considered, which is nice because it clearly delineates
# where in the code the environment is valid and will handle shtudown
# once the context exits.  The problem is that the JVM can't be
# started again, so only one such context instatiation would be
# allowed.  A regular class was also considered (not using static
# methods and state), but there is the same issue: since the JVM
# cannot be restarted, only once such instance could be created.
class GnatsEnvironment:
    """Class that provides static methods to start and stop the JVM for GNATS
    """

    # Class state variables to track (globally) whether the JVM has
    # been started and stopped
    jvm_started = False
    jvm_stopped = False

    @classmethod
    def start_jvm(cls, gnats_home=None):
        """Start java virtual machine and GNATS standalone server
        
        This function is called automatically by
        :py:class:`GnatsSimulationWrapper`, so normally there is no
        need for the user to call it directly.

        If the JVM is already running, this will do nothing.  If the
        JVM has already been stopped, this will raise an error, since
        it cannot be restarted.

        This function takes care of setting the Java classpath,
        changing directories, starting the JVM, and starting the GNATS
        standalone server.

        References to gnatsStandalone as well as other interface
        objects, which are normally available via the GNATS header
        file, are stored as attributes of the class.

        Path issues with GNATS are handled behind the scenes by setting
        the classpath and changing directories prior to starting the
        JVM.  The original directory is remembered, and it is restored
        after the JVM is stopped.

        Parameters
        ----------
        gnats_home : str, optional
            Path to GNATS home directory.  If not provided, the
            GNATS_HOME environment variable will be used.
        """
        if cls.jvm_stopped:
            raise RuntimeError("attempt to restart JVM after stopping; doing so is not allowed and will crash Java")
        if cls.jvm_started:
            # It's already started, so do nothing.  Trying to start it
            # again would cause a crash.
            return
        
        if gnats_home is None:
            GNATS_HOME = os.environ.get('GNATS_HOME')
            if GNATS_HOME is None:
                raise RuntimeError('either GNATS_HOME environment variable must be set, or gnats_home argument must be provided')
        else:
            GNATS_HOME = gnats_home        

        cls.cwd = os.getcwd() # Save current working directory

        cls.share_dir = os.path.join(GNATS_HOME, '..', 'GNATS_Server', 'share')

        # It is necssary to change directories because the GNATS
        # simulation issues a system call to "./run"
        os.chdir(os.path.abspath(GNATS_HOME))

        dist_dir = os.path.join(GNATS_HOME, 'dist')
        client_dist_dir = os.path.join(GNATS_HOME,'..','GNATS_Client','dist')

        classpath = os.path.join(dist_dir, "gnats-standalone.jar")
        classpath += os.pathsep + os.path.join(client_dist_dir, "gnats-client.jar")
        classpath += os.pathsep + os.path.join(client_dist_dir, "gnats-shared.jar")
        classpath += os.pathsep + os.path.join(client_dist_dir, "json.jar")
        classpath += os.pathsep + os.path.join(client_dist_dir, "commons-logging-1.2.jar")

        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % classpath)

        clsGNATSStandalone = jpype.JClass('GNATSStandalone')
        # Start GNATS Standalone environment
        cls.gnatsStandalone = clsGNATSStandalone.start()

        if cls.gnatsStandalone is None:
            raise RuntimeError("Can't start GNATS Standalone")

        cls._get_interfaces()

        cls.jvm_started = True

    @classmethod
    def _get_interfaces(cls):
        """Store references to interface objects"""
        cls.simulationInterface = cls.gnatsStandalone.getSimulationInterface()

        cls.entityInterface = cls.gnatsStandalone.getEntityInterface()
        cls.controllerInterface = cls.entityInterface.getControllerInterface()
        cls.pilotInterface = cls.entityInterface.getPilotInterface()

        cls.environmentInterface = cls.gnatsStandalone.getEnvironmentInterface()
        cls.airportInterface = cls.environmentInterface.getAirportInterface()
        cls.weatherInterface = cls.environmentInterface.getWeatherInterface()
        cls.terminalAreaInterface = cls.environmentInterface.getTerminalAreaInterface()
        cls.terrainInterface = cls.environmentInterface.getTerrainInterface()

        cls.equipmentInterface = cls.gnatsStandalone.getEquipmentInterface()
        cls.aircraftInterface = cls.equipmentInterface.getAircraftInterface()
        cls.cnsInterface = cls.equipmentInterface.getCNSInterface()

        cls.safetyMetricsInterface = cls.gnatsStandalone.getSafetyMetricsInterface()

        if cls.simulationInterface is None:
            raise RuntimeError("Can't get simulationInterface")

    @classmethod
    def stop_jvm(cls):
        """Stop java virtual machine and GNATS server

        This also moves back to the original directory that was set
        prior to starting the JVM

        If this function is not called manually, it will be called
        automatically at exit to make sure that the JVM is properly
        shutdown.  Multiple calls are OK.

        """
        if not cls.jvm_started:
            # Not yet started, do nothing
            return
        if cls.jvm_stopped:
            # Already started, do nothing
            return

        cls.gnatsStandalone.stop()

        # Note: have observed that calls to shutdownJVM after a jpype
        # exception can lead to a hang.  It should be safe here due to
        # the jvm_started check, but keep it in mind if reorganizing
        # the code.
        jpype.shutdownJVM()

        # Go back to where we where.  Note that calling this prior to
        # gnatsStandalone.stop() seeems to result in crashes/hangs.
        # Also note that trying to do this directory change prior to
        # writing the output file does not seem to eliminate the need
        # to fixup the paths manually.
        os.chdir(cls.cwd)

        cls.jvm_stopped = True

    @classmethod
    def get_gnats_standalone(cls):
        """Retrieve reference to GNATSStandalone class instance"""
        if not cls.jvm_started:
            raise RuntimeError("JVM not yet started")
        if cls.jvm_stopped:
            raise RuntimeError("JVM already stopped")
        return cls.gnatsStandalone

    @classmethod
    def get_gnats_constant(cls, name, classname='Constants'):
        """Return the variable that stores the named GNATS constant

        Parameters
        ----------
        name : str
            Name of GNATS constant to retrieve
        classname : str
            Name of the Java class under which the constant is defined
            (refer to the GNATS Python header file)
        """
        if not cls.jvm_started:
            raise RuntimeError("JVM not yet started")
        if cls.jvm_stopped:
            raise RuntimeError("JVM already stopped")        
        return getattr(getattr(jpype.JPackage('com').osi.util, classname), name)

    @classmethod
    def build_path(cls, filename):
        """Return a path to filename that behaves as if original directory is current working directory

        This will internally convert relative paths to be relative to
        the original working directory (otherwise, GNATS considers
        GNATS_HOME to be the working directory).
        """
        if not os.path.isabs(filename):
            filename = os.path.join(cls.cwd, filename)
        return filename
    

# Register stop_jvm to be called automatically when Python exits.
# This ensures that the JVM is shutdown properly.  The user can still
# manually call stop_jvm at any point, as it is safe to have multiple
# stop_jvm calls.
atexit.register(GnatsEnvironment.stop_jvm)


class GnatsSimulationWrapper:
    """Parent class for creating a GNATS simulation instance

    Users should implement the following methods in the derived class:
    
    simulation
      This method runs the actual GNATS simulation.  If the simulation
      code needs to access data files relative to the original working
      directory, use the :py:meth:`GnatsEnvironment.build_path`
      method, which will produce an appropriate path to work around
      the fact that GNATS simulation occurs in the GNATS_HOME
      directory.

    write_output
      This method writes output to the specified filename.

    cleanup
      Cleanup code that will be called after simulation and
      write_output.  Having cleanup code in a separate method makes it
      possible for cleanup to occur after write_output.  The cleanup
      code should not stop the GNATS standalone server or the JVM, as
      this is handled by the GnatsEnvironment class.

    Once an instance of the class is created, the simulation is run by
    calling the instance as a function, which will go to the
    :py:meth:`__call__` method.  This will call the user's simulation
    method, with additional pre- and post-processing steps.  The JVM
    will be started automatically if it is not already running.

    """

    def simulation(self):
        """Users must implement this method in the derived class

        Assume that the jvm is already started and that it will be
        shutdown by the parent class.

        The function may accept parameter values, which must be
        provided as keyword arguments when invoking
        :py:meth:`__call__`.
        """
        raise NotImplementedError("derived class must implement 'simulation' method")

    def write_output(self, filename):
        """Users must implement this method in the derived class

        It will be called after the simulation method and should issue
        the commands necessary to write the output to the specified
        file.
        """
        raise NotImplementedError("derived class must implement 'write_output' method")

    def __call__(self, output_file=None, return_df=True, **kwargs):

        """Execute GNATS simulation and write output to specified file

        Parameters
        ----------
        output_file : str
            Output file to write to.  If not provided, a temporary file is used
        return_df : bool
            Whether to read the output into a DataFrame and return it
        **kwargs
            Extra keyword arguments to pass to simulation call

        Returns
        -------
        dict
            A dictionary with the following keys:
                'trajectory' (if return_df==True)
                    DataFrame with trajectory results
                'sim_results'
                    Return value from child simulation method
        """
        # Make sure that the JVM has been started.  This is safe to
        # call even if it has already been started.
        GnatsEnvironment.start_jvm()

        results = dict()
        
        results['sim_results'] = self.simulation(**kwargs)

        if output_file is None:
            # Create a temporary directory to store the output, so it
            # can be read back
            tempdir = tempfile.mkdtemp()
            output_file = os.path.join(tempdir, 'gnats.csv')
        else:
            tempdir = None

        try:
            self.write_output(GnatsEnvironment.build_path(output_file))
            if return_df:
                df = read_gnats_output_file(GnatsEnvironment.build_path(output_file))
        finally:
            # This ensures we clean up the temporary directory and
            # file even if an exception occurs above.  If there is an
            # exception, it is automatically re-raised after finally.
            if tempdir:
                if os.path.isfile(output_file):
                    os.remove(output_file)
                os.rmdir(tempdir)

        if hasattr(self, 'cleanup'):
            self.cleanup()

        if return_df:
            results['trajectory'] = df

        return results


class GnatsBasicSimulation(GnatsSimulationWrapper):
    """Simple interface for running a GNATS simulation from TRX and MFL files

    If more control is needed, create a subclass of :py:class:`GnatsSimulationWrapper`"""
    def __init__(self, trx_file, mfl_file, propagation_time, time_step):
        """Define basic simulation

        Parameters
        ----------
        trx_file : str
        mfl_file : str
        propagation_time : int
            Total flight propagation time in seconds
        time_step : int
            Time step in seconds
        """
        
        self.trx_file = trx_file
        self.mfl_file = mfl_file
        self.propagation_time = propagation_time
        self.time_step = time_step

    def simulation(self):
        GNATS_SIMULATION_STATUS_ENDED = GnatsEnvironment.get_gnats_constant('GNATS_SIMULATION_STATUS_ENDED')

        simulationInterface = GnatsEnvironment.simulationInterface
        environmentInterface = GnatsEnvironment.environmentInterface
        aircraftInterface = GnatsEnvironment.aircraftInterface

        simulationInterface.clear_trajectory()

        environmentInterface.load_rap(GnatsEnvironment.share_dir + "/tg/rap")

        aircraftInterface.load_aircraft(self.trx_file, self.mfl_file)

        simulationInterface.setupSimulation(self.propagation_time, self.time_step)

        simulationInterface.start()

        while True:
            runtime_sim_status = simulationInterface.get_runtime_sim_status()
            if (runtime_sim_status == GNATS_SIMULATION_STATUS_ENDED) :
                break
            else:
                time.sleep(1)

    def write_output(self, filename):
        GnatsEnvironment.simulationInterface.write_trajectories(filename)

    def cleanup(self):
        GnatsEnvironment.aircraftInterface.release_aircraft()
        GnatsEnvironment.environmentInterface.release_rap()

def read_gnats_output_file(filename):
    """Read the specified GNATS output file

    Parameters
    ----------
    filename : str
        Input file to read

    Returns
    -------
    Single formatted data frame"""

    # Read all lines:
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Read header information out of specific line numbers
    header_cols = lines[4].strip()[3:].split(',')
    data_cols = lines[5].strip()[3:].split(',')
    start_time = int(lines[7])

    # Store all lines after header
    lines = lines[9:]

    # Flag header lines, which may occur throughout the file
    is_header_line = [line.split(',')[0].isalpha() for line in lines]
    header_indices = np.where(is_header_line)[0]

    # Read in data by iterating over the header rows.  Each header row
    # specifies the number of records that follow.  That number is
    # used to find the corresponding subset of data lines associated
    # with the header, and those lines are read in as a DataFrame
    # according to the column names defined above.
    df = pd.DataFrame(columns=data_cols + ['callsign','origin','destination'])
    for header_idx in header_indices:
        header_row = pd.read_csv(StringIO(lines[header_idx]), header=None, names=header_cols).iloc[0]
        nrows = header_row['number_of_trajectory_rec']
        aircraft_df = pd.read_csv(StringIO('\n'.join(lines[header_idx+1:header_idx+1+nrows])), header=None, names=data_cols)

        # Fill in auxiliary data that comes from the header row
        aircraft_df['callsign'] = header_row['callsign']
        aircraft_df['origin'] = header_row['origin_airport']
        aircraft_df['destination'] = header_row['destination_airport']
        # Adjust for aircraft-specific start time:
        aircraft_df['timestamp(UTC sec)'] += header_row['start_time']

        # Append this aircraft's data to the output:
        df = df.append(aircraft_df)


    df.rename(columns={'timestamp(UTC sec)':'time',
                       'course':'heading',
                       'rocd_fps':'rocd',
                       'sector_name':'sector',
                       'tas_knots':'tas',
                       'flight_phase':'status',
                       'altitude_ft':'altitude'},
              inplace=True)
    df['time'] += start_time
    df['time'] = pd.to_datetime(df['time'], unit='s')

    return df


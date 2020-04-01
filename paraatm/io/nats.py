"""Functions for interfacing to NATS simulation"""

import pandas as pd
import numpy as np
from io import StringIO
import os
import jpype
import tempfile
import atexit


# Note: NatsEnvironment is implemented as a class wtih static methods.
# The same effect could be achieved using globally defined functions
# and state variables, but the class is used in order to provide some
# organization and encapuslation.
#
# Implementation of these utilities was challenging because the JVM
# and NATS servers can only be started once.  After they are stopped,
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
class NatsEnvironment:
    """Class that provides static methods to start and stop the JVM for NATS
    """

    # Class state variables to track (globally) whether the JVM has
    # been started and stopped
    jvm_started = False
    jvm_stopped = False

    @classmethod
    def start_jvm(cls, nats_home=None):
        """Start java virtual machine and NATS standalone server
        
        This function is called automatically by
        :py:class:`NatsSimulationWrapper`, so normally there is no
        need for the user to call it directly.

        If the JVM is already running, this will do nothing.  If the
        JVM has already been stopped, this will raise an error, since
        it cannot be restarted.

        This function takes care of setting the Java classpath,
        changing directories, starting the JVM, and starting the NATS
        standalone server.

        Path issues with NATS are handled behind the scenes by setting
        the classpath and changing directories prior to starting the
        JVM.  The original directory is remembered, and it is restored
        after the JVM is stopped.

        Parameters
        ----------
        nats_home : str, optional
            Path to NATS home directory.  If not provided, the
            NATS_HOME environment variable will be used.
        """
        if cls.jvm_stopped:
            raise RuntimeError("attempt to restart JVM after stopping; doing so is not allowed and will crash Java")
        if cls.jvm_started:
            # It's already started, so do nothing.  Trying to start it
            # again would cause a crash.
            return
        
        if nats_home is None:
            NATS_HOME = os.environ.get('NATS_HOME')
            if NATS_HOME is None:
                raise RuntimeError('either NATS_HOME environment variable must be set, or nats_home argument must be provided')
        else:
            NATS_HOME = nats_home        
        
        cls.cwd = os.getcwd() # Save current working directory

        # It is necssary to change directories because the NATS
        # simulation issues a system call to "./run"
        os.chdir(os.path.abspath(NATS_HOME))

        classpath = os.path.join(NATS_HOME, "dist/nats-standalone.jar")
        classpath = classpath + ":" + os.path.join(NATS_HOME, "dist/nats-client.jar")
        classpath = classpath + ":" + os.path.join(NATS_HOME, "dist/nats-shared.jar")
        classpath = classpath + ":" + os.path.join(NATS_HOME, "dist/json.jar")
        classpath = classpath + ":" + os.path.join(NATS_HOME, "dist/commons-logging-1.2.jar")

        jpype.startJVM(jpype.getDefaultJVMPath(), "-ea", "-Djava.class.path=%s" % classpath)

        clsNATSStandalone = jpype.JClass('NATSStandalone')
        # Start NATS Standalone environment
        cls.natsStandalone = clsNATSStandalone.start()

        if cls.natsStandalone is None:
            raise RuntimeError("Can't start NATS Standalone")

        cls.jvm_started = True

    @classmethod
    def stop_jvm(cls):
        """Stop java virtual machine and NATS server

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

        cls.natsStandalone.stop()

        # Note: have observed that calls to shutdownJVM after a jpype
        # exception can lead to a hang.  It should be safe here due to
        # the jvm_started check, but keep it in mind if reorganizing
        # the code.
        jpype.shutdownJVM()

        # Go back to where we where.  Note that calling this prior to
        # natsStandalone.stop() seeems to result in crashes/hangs.
        # Also note that trying to do this directory change prior to
        # writing the output file does not seem to eliminate the need
        # to fixup the paths manually.
        os.chdir(cls.cwd)

        cls.jvm_stopped = True

    @classmethod
    def get_nats_standalone(cls):
        """Retrieve reference to NATSStandalone class instance"""
        if not cls.jvm_started:
            raise RuntimeError("JVM not yet started")
        if cls.jvm_stopped:
            raise RuntimeError("JVM already stopped")
        return cls.natsStandalone

    @classmethod
    def get_nats_constant(cls, name):
        """Return the variable that stores the named NATS constant

        Parameters
        ----------
        name : str
            Name of NATS constant to retrieve
        """
        if not cls.jvm_started:
            raise RuntimeError("JVM not yet started")
        if cls.jvm_stopped:
            raise RuntimeError("JVM already stopped")        
        return getattr(jpype.JPackage('com').osi.util.Constants, name)

    

# Register stop_jvm to be called automatically when Python exits.
# This ensures that the JVM is shutdown properly.  The user can still
# manually call stop_jvm at any point, as it is safe to have multiple
# stop_jvm calls.
atexit.register(NatsEnvironment.stop_jvm)


class NatsSimulationWrapper:
    """Parent class for creating a NATS simulation instance

    Users should implement the following methods in the derived class:
    
    simulation
      This method runs the actual NATS simulation.  If the simulation
      code needs to access data files relative to the original working
      directory, use the :py:meth:`get_path` method, which will
      produce an appropriate path to work around the fact that NATS
      simulation occurs in the NATS_HOME directory.

    write_output
      This method writes output to the specified filename.

    cleanup
      Cleanup code that will be called after simulation and
      write_output.  Having cleanup code in a separate method makes it
      possible for cleanup to occur after write_output.  The cleanup
      code should not stop the NATS standalone server or the JVM, as
      this is handled by the NatsEnvironment class.

    Once an instance of the class is created, the simulation is run by
    calling the instance as a function, which will go to the
    :py:meth:`__call__` method.  This will call the user's simulation
    method, with additional pre- and post-processing steps.  The JVM
    will be started automatically if it is not already running.

    """

    def simulation(self, *args, **kwargs):
        """Users must implement this method in the derived class

        Assume that the jvm is already started and that it will be
        shutdown by the parent class.
        """
        raise NotImplementedError("derived class must implement 'simulation' method")

    def write_output(self, filename):
        """Users must implement this method in the derived class

        It will be called after the simulation method and should issue
        the commands necessary to write the output to the specified
        file.
        """
        raise NotImplementedError("derived class must implement 'write_output' method")

    def __call__(self, output_file=None, return_df=True, *args, **kwargs):

        """Execute NATS simulation and write output to specified file

        Parameters
        ----------
        output_file : str
            Output file to write to.  If not provided, a temporary file is used
        return_df : bool
            Whether to read the output into a DataFrame and return it

        Returns
        -------
        DataFrame
            If return_df is True, read the output into a DataFrame and
            return that
        """
        # Make sure that the JVM has been started.  This is safe to
        # call even if it has already been started.
        NatsEnvironment.start_jvm()
        
        self.simulation(*args, **kwargs)

        if output_file is None:
            # Create a temporary directory to store the output, so it
            # can be read back
            tempdir = tempfile.mkdtemp()
            output_file = os.path.join(tempdir, 'nats.csv')
        else:
            tempdir = None

        try:
            self.write_output(self.get_path(output_file))
            if return_df:
                df = read_nats_output_file(output_file)
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
            return df


    def get_path(self, filename):
        """Return a path to filename that behaves as if original directory is current working directory

        This will internally convert relative paths to be relative to
        the original working directory (otherwise, NATS considers
        NATS_HOME to be the working directory).
        """
        if not os.path.isabs(filename):
            filename = os.path.join(self.cwd, filename)
        return filename



def read_nats_output_file(filename):
    """Read the specified NATS output file

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

    # Keep only selected columns
    selected_cols = ['time','callsign','origin','destination','latitude','longitude','altitude','rocd','tas','heading','sector','status']
    df = df[selected_cols]

    return df


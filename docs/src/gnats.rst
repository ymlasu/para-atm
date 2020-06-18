.. _gnats:

GNATS simulation
================

.. py:module:: paraatm.io.gnats

`para-atm` includes capabilities to facilitate running the `GNATS <https://github.com/OptimalSynthesisInc/GNATS>`__ simulation from within Python.  These capabilities are provided by the :py:mod:`paraatm.io.gnats` module.  The following functionality is provided:

* Boilerplate code to automatically start and stop the Java virtual machine, and to prevent it from being started multiple times
* Behind-the-scenes path handling, so that the GNATS simulation does not need to be run from within the GNATS installation directory
* A utility function to retrieve GNATS constants from the Java environment
* Return trajectory results directly as a pandas DataFrame

The functions for interfacing with GNATS are subject to change.  Currently, the code has been tested with GNATS beta1.10 on Ubuntu Linux.

Creating a GNATS simulation
---------------------------

Creation of a GNATS simulation in `para-atm` is done by writing a class that derives from the :py:class:`~paraatm.io.gnats.GnatsSimulationWrapper` class.  This is best understood through an example.  The complete code for the following example is available at `tests/gnats_gate_to_gate.py`, and it is based on `DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.9.py` from the GNATS `samples` directory. 

.. code-block:: python
   :linenos:
     
    from paraatm.io.gnats import GnatsSimulationWrapper, GnatsEnvironment

    class GateToGate(GnatsSimulationWrapper):
        def simulation(self):

            GNATS_SIMULATION_STATUS_PAUSE = GnatsEnvironment.get_gnats_constant('GNATS_SIMULATION_STATUS_PAUSE')
            GNATS_SIMULATION_STATUS_ENDED = GnatsEnvironment.get_gnats_constant('GNATS_SIMULATION_STATUS_ENDED')

            DIR_share = GnatsEnvironment.share_dir

            simulationInterface = GnatsEnvironment.simulationInterface
            environmentInterface = GnatsEnvironment.environmentInterface
            aircraftInterface = GnatsEnvironment.aircraftInterface        
            # ...

In this example, Line 3 defines the :py:class:`GateToGate` class as a subclass of :py:class:`~paraatm.io.gnats.GnatsSimulationWrapper` class.  Then, the :py:meth:`simulation` method is defined.  This is where the user's code for setting up and running the GNATS simulation should go.  Notice that lines 6 and 7 use the :py:meth:`~paraatm.io.gnats.GnatsEnvironment.get_gnats_constant` method to retrieve specific constants from the Java environment, which are used later in the simulation code.

Line 9 gets a reference to the location of the "share" directory used by GNATS.  Lines 11-13 retrieve references to the interface objects, which are available through :py:class:`~paraatm.io.gnats.GnatsEnvironment`.  The bulk of the remaining code follows the example file that is included with GNATS.

As compared to the GNATS sample file, some key differences in this implementation are:

* :code:`from GNATS_Python_Header_standalone import *` is not used (in general, :code:`import *` is not advisable)
* Cleanup calls for :code:`gnatsStandalone.stop()` and :code:`shutdownJVM()` are not needed, as they are automatically handled
* GNATS constants are retrieved using the utility function :py:meth:`~paraatm.io.gnats.GnatsEnvironment.get_gnats_constant`, as opposed to importing the constants from `GNATS_Python_Header_standalone.py`, where each constant is manually defined


Running the GNATS simulation
----------------------------

Once the user-defined class deriving from :py:class:`~paraatm.io.gnats.GnatsSimulationWrapper` has been created, the simulation is executed by creating an instance of the class and calling its :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.__call__` method.  This method will handle various setup behind the scenes, such as starting the JVM, creating the :code:`GNATSStandalone` instance, and preparing the current working directory.  Once the simulation is prepared, the user's :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.simulation` method is called automatically.  The output file is automatically created by communicating with the user-defined :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.write_output` method, and the trajectory results are stored as a DataFrame in the :code:`'trajectory'` key of the returned dictionary.

For example, the :py:class:`GateToGate` simulation class defined above could be invoked as:

.. code-block:: python
   :linenos:

   g2g_sim = GateToGate()
   df = g2g_sim()['trajectory']

Here, line 1 creates an instance of the :py:class:`GateToGate` class.  Line 2 executes the simulation, passing no arguments (note that the :code:`()` operator invokes the :code:`__call__` method).  The return value of :code:`g2g_sim()` is a dictionary, and we retrieve the value of the :code:`'trajectory'` key, which is a DataFrame that stores the resulting trajectory data.  Note that line 2 is just shorthand for:


.. code-block:: python

   results = g2g_sim()
   df = results['trajectory']

Additional keyword arguments provided to :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.__call__` are passed on to :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.simulation`.  This makes it possible to create a simulation instance that accepts parameter values.  For example:

.. code-block:: python
   :linenos:

   class MySim(GnatsSimulationWrapper):
       def simulation(self, my_parameter):
           # .. Perform simulation using the value of my_parameter

   my_sim = MySim()
   df1 = my_sim(my_parameter=1)
   df2 = my_sim(my_parameter=2)

Here, the user-defined :py:meth:`simulation` method on line 2 is defined to accept an argument, :code:`my_parameter`.  Once the simulation class is instantiated, repeated calls can be made using different parameter values, as shown on lines 6 and 7.

If the simulation method itself returns values, :py:meth:`~paraatm.io.gnats.GnatsSimulationWrapper.__call__` stores these in the :code:`'sim_results'` key of the dictionary that it returns.  For example:

.. code-block:: python
    :linenos:

    class MySimWithReturnVals(GnatsSimulationWrapper):
        def simulation(self):
            # .. Perform simulation
            return some_data

    my_sim = MySimWithReturnVals()
    some_data = my_sim(return_df=False)['sim_results']

In this example, the call to :code:`my_sim()` on line 7 uses the :code:`return_df=False` option to suppress storing the trajectory results.  However, this is not required, and both trajectory results and custom return values can be returned if needed.


The API
-------

.. autoclass:: paraatm.io.gnats.GnatsSimulationWrapper
    :members:
    :special-members:
    :exclude-members: __weakref__

.. autoclass:: paraatm.io.gnats.GnatsEnvironment
    :members:

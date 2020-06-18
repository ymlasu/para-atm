.. _nats:

NATS simulation
===============

.. py:module:: paraatm.io.nats

`para-atm` includes capabilities to facilitate running the NATS simulation from within Python.  These capabilities are provided by the :py:mod:`paraatm.io.nats` module.  The following functionality is provided:

* Boilerplate code to automatically start and stop the Java virtual machine, and to prevent it from being started multiple times
* Behind-the-scenes path handling, so that the NATS simulation does not need to be run from within the NATS installation directory
* A utility function to retrieve NATS constants from the Java environment
* Return trajectory results directly as a pandas DataFrame

The functions for interfacing with NATS are subject to change.  Currently, the code has been tested with NATS 1.7beta and NATS 1.8beta on Ubuntu Linux.

Creating a NATS simulation
--------------------------

Creation of a NATS simulation in `para-atm` is done by writing a class that derives from the :py:class:`~paraatm.io.nats.NatsSimulationWrapper` class.  This is best understood through an example.  The complete code for the following example is available at `tests/nats_gate_to_gate.py`, and it is based on `DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.7.py` from the NATS `samples` directory. 

.. code-block:: python
   :linenos:
     
    from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment

    class GateToGate(NatsSimulationWrapper):
        def simulation(self):

            NATS_SIMULATION_STATUS_PAUSE = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_PAUSE')
            NATS_SIMULATION_STATUS_ENDED = NatsEnvironment.get_nats_constant('NATS_SIMULATION_STATUS_ENDED')

            natsStandalone = NatsEnvironment.get_nats_standalone()

            simulationInterface = natsStandalone.getSimulationInterface()
            # ...

In this example, Line 3 defines the :py:class:`GateToGate` class as a subclass of :py:class:`~paraatm.io.nats.NatsSimulationWrapper` class.  Then, the :py:meth:`simulation` method is defined.  This is where the user's code for setting up and running the NATS simulation should go.  Notice that lines 6 and 7 use the :py:meth:`~paraatm.io.nats.NatsEnvironment.get_nats_constant` method to retrieve specific constants from the Java environment, which are used later in the simulation code.

Line 9 gets a reference to the :code:`natsStandalone` instance, which is then used to access other simulation objects.  The bulk of the remaining code follows the example file that is included with NATS.

As compared to the NATS sample file, some key differences in this implementation are:

* :code:`from NATS_Python_Header import *` is not used (in general, :code:`import *` is not advisable)
* Calls to :code:`JClass('NATSStandalone')` and :code:`clsNATSStandalone.start()` are not needed, as they are handled automatically by the :py:class:`~paraatm.io.nats.NatsSimulationWrapper` class 
* :code:`NatsEnvironment.get_nats_standalone()` is used to retrieve a reference to the NATS standalone environment, which has already been started by the wrapper class 
* Cleanup calls for :code:`natsStandalone.stop()` and :code:`shutdownJVM()` are not needed, as they are automatically handled as well
* NATS constants are retrieved using the utility function :py:meth:`~paraatm.io.nats.NatsEnvironment.get_nats_constant`, as opposed to importing the constants from `NATS_Python_Header.py`, where each constant is manually defined


Running the NATS simulation
---------------------------

Once the user-defined class deriving from :py:class:`~paraatm.io.nats.NatsSimulationWrapper` has been created, the simulation is executed by creating an instance of the class and calling its :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.__call__` method.  This method will handle various setup behind the scenes, such as starting the JVM, creating the :code:`NATSStandalone` instance, and preparing the current working directory.  Once the simulation is prepared, the user's :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.simulation` method is called automatically.  The output file is automatically created by communicating with the user-defined :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.write_output` method, and the trajectory results are stored as a DataFrame in the `'trajectory'` key of the returned dictionary.

For example, the :py:class:`GateToGate` simulation class defined above could be invoked as:

.. code-block:: python
   :linenos:

   g2g_sim = GateToGate()
   df = g2g_sim()['trajectory']

Here, line 1 creates an instance of the :py:class:`GateToGate` class.  Line 2 executes the simulation, passing no arguments (note that the :code:`()` operator invokes the :code:`__call__` method).  The return value of `g2g_sim()` is a dictionary, and we retrieve the value of the `'trajectory'` key, which is a DataFrame that stores the resulting trajectory data.  Note that Line 2 is just shorthand for:

.. code-block:: python

    results = g2g_sim()
    df = results['trajectory']

Additional keyword arguments provided to :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.__call__` are passed on to :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.simulation`.  This makes it possible to create a simulation instance that accepts parameter values.  For example:

.. code-block:: python
   :linenos:

   class MySim(NatsSimulationWrapper):
       def simulation(self, my_parameter):
           # .. Perform simulation using the value of my_parameter

   my_sim = MySim()
   df1 = my_sim(my_parameter=1)['trajectory']
   df2 = my_sim(my_parameter=2)['trajectory']

Here, the user-defined :py:meth:`simulation` method on line 2 is defined to accept an argument, :code:`my_parameter`.  Once the simulation class is instantiated, repeated calls can be made using different parameter values, as shown on lines 6 and 7.

If the simulation method itself returns values, :py:meth:`~paraatm.io.nats.NatsSimulationWrapper.__call__` stores these in the `'sim_results'` key of the dictionary that it returns.  For example:

.. code-block:: python
    :linenos:

    class MySimWithReturnVals(NatsSimulationWrapper):
        def simulation(self):
            # .. Perform simulation
            return some_data

    my_sim = MySimWithReturnVals()
    some_data = my_sim(return_df=False)['sim_results']

In this example, the call to `my_sim` on line 7 uses the `return_df=False` option to suppress storing the trajectory results.  However, this is not required, and both trajectory results and custom return values can be returned if needed.


The API
-------

.. autoclass:: paraatm.io.nats.NatsSimulationWrapper
    :members:
    :special-members:
    :exclude-members: __weakref__

.. autoclass:: paraatm.io.nats.NatsEnvironment
    :members:

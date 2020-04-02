.. _nats:

NATS Simulation
===============

.. py:module:: paraatm.io.nats

`para-atm` includes capabilities to facilitate running the NATS simulation from within Python.  These capabilities are provided by the :py:mod:`paraatm.io.nats` module.  The following functionality is provided:

* Boilerplate code to automatically start and stop the Java virtual machine, and to prevent it from being started multiple times
* Behind-the-scenes path handling, so that the NATS simulation does not need to be run from within the NATS installation directory
* A utility function to retrieve NATS constants from the Java environment
* Return simulation results directly as a pandas DataFrame

The functions for interfacing with NATS are subject to change.  Currently, the code has been tested with NATS 1.7beta and NATS 1.8beta on Ubuntu Linux.

Creating a NATS simulation
--------------------------

Creation of a NATS simulation in `para-atm` is done by writing a class that derives from the :py:class:`~paraatm.io.nats.NatsSimulationWrapper` class.  This is best understood through an example.  The complete code for the following example is available at `tests/nats_gate_to_gate.py`, and it is based on `DEMO_Gate_To_Gate_Simulation_SFO_PHX_beta1.7.py` from the NATS `samples` directory. 

.. code-block:: python
   :linenos:
     
    from paraatm.io.nats import NatsSimulationWrapper, NatsEnvironment

    class GateToGate(NatsSimulationWrapper):
        def simulation(self, *args, **kwargs):

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



The API
-------

.. autoclass:: paraatm.io.nats.NatsSimulationWrapper
    :members:
    :special-members:
    :exclude-members: __weakref__

.. autoclass:: paraatm.io.nats.NatsEnvironment
    :members:

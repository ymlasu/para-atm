import unittest
import pandas as pd
import numpy as np
import os
import torch
from paraatm.io.nats import read_nats_output_file, NatsEnvironment
from paraatm.io.gnats import read_gnats_output_file, GnatsEnvironment
from paraatm.io.iff import read_iff_file
from paraatm.io.utils import read_csv_file
from paraatm.safety.ground_ssd import ground_ssd_safety_analysis
from paraatm.rsm.gp import SklearnGPRegressor
from paraatm.simulation_method.vcas import VCAS
from paraatm.simulation_method.aviationr import AviationRisk

from . import nats_gate_to_gate
from . import gnats_gate_to_gate

# Change this to False to test NATS instead of GNATS
USE_GNATS = True

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sample_nats_file = os.path.join(THIS_DIR, '..', 'sample_data/NATS_output_SFO_PHX.csv')
sample_gnats_file = os.path.join(THIS_DIR, '..', 'sample_data/GNATS_output_SFO_PHX.csv')

class TestNATSFiles(unittest.TestCase):
    def test_read_nats_output(self):
        df = read_nats_output_file(sample_nats_file)
        # Simple check:
        self.assertEqual(len(df), 369)

    def test_read_nats_output_5ac(self):
        filename = os.path.join(THIS_DIR, '..', 'sample_data/NATS_demo_5_aircraft.csv')
        df = read_nats_output_file(filename)
        # Perform some basic consistency checks:
        self.assertEqual(len(df), 510)
        self.assertEqual(len(df['callsign'].unique()), 5)
        self.assertEqual(df.isnull().sum().sum(), 0)

class TestGNATSFiles(unittest.TestCase):
    def test_read_gnats_output(self):
        df = read_gnats_output_file(sample_gnats_file)
        # Simple check:
        self.assertEqual(len(df), 218)
        
class TestIFFFiles(unittest.TestCase):
    def test_read_iff(self):
        filename = os.path.join(THIS_DIR, '..', 'sample_data/IFF_SFO_ASDEX_ABC123.csv')
        df_dict = read_iff_file(filename, 'all')

        expected_rows = {0:1, 1:1, 2:1, 3:724, 4:6}

        # Basic consistency check on number of entries for each record:
        for rec, df in df_dict.items():
            self.assertEqual(len(df), expected_rows[rec])

    def test_read_iff_callsigns(self):
        filename = os.path.join(THIS_DIR, '..', 'sample_data/IFF_SFO_ASDEX_3aircraft.csv')

        df = read_iff_file(filename, callsigns='ABC123')
        self.assertEqual(len(df), 194)
        self.assertEqual(len(df['callsign'].unique()), 1)

        df = read_iff_file(filename, callsigns=['DEF456','GHI789'])
        self.assertEqual(len(df), 372)
        self.assertEqual(len(df['callsign'].unique()), 2)

class TestGroundSSD(unittest.TestCase):
    def test_ground_ssd(self):
        filename = os.path.join(THIS_DIR, '..', 'sample_data/IFF_SFO_window.csv')
        df = read_csv_file(filename)
        safety = ground_ssd_safety_analysis(df)

        # Basic consistency checks:
        self.assertEqual(len(safety['callsign'].unique()), 16)
        self.assertTrue(all(safety['fpf'] <= 1.0))
        self.assertTrue(all(safety['fpf'] >= 0.0))
        self.assertEqual(sum(safety['fpf'].isnull()), 0)

@unittest.skipIf(USE_GNATS, "use GNATS instead of NATS")
class TestNatsSimulation(unittest.TestCase):
    # Note that for this test to run, NATS must be installed and the
    # NATS_HOME environment variable must be set appropriately

    # Although the JVM will be shutdown automatically at program exit,
    # we do it manually here to restore the current working directory,
    # in case subsequent tests depend on it.
    @classmethod
    def tearDownClass(cls):
        NatsEnvironment.stop_jvm()
    
    def test_gate_to_gate(self):
        simulation = nats_gate_to_gate.GateToGate()
        df = simulation()

        # Basic consistency checks:
        self.assertEqual(len(df), 369)

    # Note from McFarland: testing on Ubuntu using NATS 1.8, this test
    # often hangs after the message "Flight propagation completed",
    # with CPU still being utilized but no further progress.  The hang
    # occurs sometimes but other times the test completes.  This
    # should be investigated further.  Perhaps it will be resolved by
    # moving to GNATS.
    def test_vcas(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(cur_dir, '..', 'sample_data/')
        cfg = {'fp_file': data_dir + 'vcas/ASU123at6000.trx',  # flight plan file
               'mfl_file': data_dir + 'vcas/ASU123_mfl.trx',  # mfl file
               'cmd_file': data_dir + 'vcas/command.csv',  # text command
               'data_file': data_dir + 'vcas/ASU123.csv',  # actual trajectory data
               'sim_time': 1000}  # total simulation time

        sim = VCAS(cfg)
        track = sim()
        self.assertEqual(len(track), 1000)
    def test_aviationr(self):
        cur_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(cur_dir, '..', 'sample_data/')

        cfg = {'fp_file': data_dir + 'aviationR/data/TRX_DEMO_SFO_PHX_GateToGate.trx',  # flight plan file
               'mfl_file': data_dir + 'aviationR/data/TRX_DEMO_SFO_PHX_mfl.trx',  # mfl file
               'data_file': data_dir + 'aviationR/data/',
               'model_file': data_dir + 'aviationR/model/',
               'sim_time': 1000}  # total simulation time

        # call
        sim = AviationRisk(cfg)
        device = torch.device('cpu')
        if torch.cuda.is_available():
            device = torch.device('cuda')
        _ = sim.simulation(device)  # call simulation function using NatsSimulationWrapper

@unittest.skipIf(not USE_GNATS, "use NATS instead of GNATS")
class TestGnatsSimulation(unittest.TestCase):
    # Note that for this test to run, GNATS must be installed and the
    # GNATS_HOME environment variable must be set appropriately

    # Although the JVM will be shutdown automatically at program exit,
    # we do it manually here to restore the current working directory,
    # in case subsequent tests depend on it.
    @classmethod
    def tearDownClass(cls):
       GnatsEnvironment.stop_jvm()

    def test_gate_to_gate(self):
        simulation = gnats_gate_to_gate.GateToGate()
        df = simulation()

        # Basic consistency checks:
        self.assertEqual(len(df), 218)

class TestSklearnGP(unittest.TestCase):
    def test_1d(self):
        x = np.array([1., 3., 5., 6., 7., 8.])
        y = x * np.sin(x)
        X = x[:,np.newaxis] # Make input array 2d

        # Use n_restarts_optimizer to get reproducible behavior
        gp = SklearnGPRegressor(X, y, n_restarts_optimizer=0)

        # Test out various parts of the __call__ API

        ym = gp([2.0])
        # Using only a low precision here as a basic test.  Not trying
        # to verify that we get exactly the same result every time.
        self.assertAlmostEqual(ym, 1.435301, 1)

        ym, ys = gp([2.0], return_stdev=True)
        self.assertAlmostEqual(ym, 1.435301, 1)
        self.assertAlmostEqual(ys, 0.805718, 1)

        Ym = gp([[2.0], [2.0]])
        self.assertAlmostEqual(Ym[0], 1.435301, 1)
        self.assertAlmostEqual(Ym[1], 1.435301, 1)

        Ym, Ys = gp([[2.0], [2.0]], return_stdev=True)
        self.assertAlmostEqual(Ym[0], 1.435301, 1)
        self.assertAlmostEqual(Ym[1], 1.435301, 1)
        self.assertAlmostEqual(Ys[0], 0.805718, 1)
        self.assertAlmostEqual(Ys[1], 0.805718, 1)
        
if __name__ == '__main__':
    unittest.main()

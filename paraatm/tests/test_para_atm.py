import unittest
import pandas as pd
import numpy as np
import os

from paraatm.io.nats import read_nats_output_file, NatsEnvironment
from paraatm.io.iff import read_iff_file
from paraatm.io.utils import read_csv_file
from paraatm.safety.ground_ssd import ground_ssd_safety_analysis

from .nats_gate_to_gate import GateToGate
from paraatm.simulation_method.vcas import VCAS

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sample_nats_file = os.path.join(THIS_DIR, '..', 'sample_data/NATS_output_SFO_PHX.csv')

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
        simulation = GateToGate()
        df = simulation()

        # Basic consistency checks:
        self.assertEqual(len(df), 369)

class TestVCASsimulation(unittest.TestCase):
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


if __name__ == '__main__':
    unittest.main()

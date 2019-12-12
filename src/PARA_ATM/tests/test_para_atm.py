import unittest
import pandas as pd
import numpy as np
import os

from PARA_ATM.Commands.Helpers.DataStore import Access
from PARA_ATM.Application import LaunchApp
from PARA_ATM.io.nats import read_nats_output_file
from PARA_ATM.io.iff import read_iff_file

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sample_nats_file = os.path.join(THIS_DIR, '..', 'sample_data/NATS_output_SFO_PHX.csv')

class TestApp(unittest.TestCase):
    def setUp(self):
        self.container = LaunchApp.Container()
        self.db_access = Access()

    def tearDown(self):
        # Ensure table is removed even if test fails (safe to call on non-existent table)
        self.db_access.dropTable('test_table')
    
    def test_construction(self):
        """Test construction of LaunchApp container"""
        # Verify that the Container constructor runs without error.
        # In future, could add assertions that check specific
        # attributes of the result (e.g. that some of the
        # widgets/tables have certain characteristics), but for now
        # the test is soley used to verify that exceptions do not
        # occur during creation of the container.

        # Although there is no code here, this is kept as a separate
        # test to differentiate between errors in container creation
        # that happen in setUp, versus errors in functions tested via
        # other test cases.
        pass

    def testTableSelect(self):
        """Test the callback when the table selection changes"""
        
        # First we need to ensure there is a valid table in the
        # database, so we do this by reading in a sample NATS output
        # file and adding it to the database
        df = read_nats_output_file(sample_nats_file)
        self.db_access.addTable('test_table', df)

        # Try and select the new table
        self.container.tables.value = 'test_table'


class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_access = Access()

    def tearDown(self):
        # Ensure table is removed even if test fails (safe to call on non-existent table)
        self.db_access.dropTable('test_table')        

    def testTableNotExists(self):
        self.assertFalse(self.db_access.tableExists('nonexistent_table'))

    def testAddReadDrop(self):
        """Add a table, read it, then drop it"""
        # Add a table
        df1 = pd.DataFrame(np.eye(3))
        self.db_access.addTable('test_table', df1, index=False)

        # Verify that it exists
        self.assertTrue(self.db_access.tableExists('test_table'))

        # Read it back
        df2 = self.db_access.readTable('test_table')
        self.assertTrue(np.all(df1.values==df2.values))

        # Drop it
        self.db_access.dropTable('test_table')

        # Verify that it doesn't exist
        self.assertFalse(self.db_access.tableExists('test_table'))

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
        
if __name__ == '__main__':
    unittest.main()

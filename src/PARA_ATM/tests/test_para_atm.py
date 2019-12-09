import unittest
import pandas as pd
import numpy as np

from PARA_ATM.Commands.Helpers.DataStore import Access
from PARA_ATM.Application import LaunchApp

class TestLaunchApp(unittest.TestCase):
    def test(self):
        """Test construction of LaunchApp container"""
        # Verify that the Container constructor runs without error.
        # In future, could add assertions that check specific
        # attributes of the result (e.g. that some of the
        # widgets/tables have certain characteristics), but for now
        # the test is soley used to verify that exceptions do not
        # occur during creation of the container.
        c = LaunchApp.Container()

class TestDB(unittest.TestCase):
    def setUp(self):
        self.db_access = Access()

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
        
        

if __name__ == '__main__':
    unittest.main()

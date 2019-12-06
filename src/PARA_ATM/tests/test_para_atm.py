import unittest

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

if __name__ == '__main__':
    unittest.main()

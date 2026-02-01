"""
Created on 2026-02-01

@author: wf
"""
from basemkit.basetest import Basetest
from wmg.cli import WalkMyGraphCmd
from wmg.version import Version

class TestCli(Basetest):
    """
    test command line handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testVersion(self):
        """
        test the version
        """
        version=Version()
        cmd = WalkMyGraphCmd(version)
        self.assertIn(version.name, cmd.version_msg)
        self.assertIn(version.version, cmd.version_msg)

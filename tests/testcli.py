"""
Created on 2026-02-01

@author: wf
"""

import contextlib
import io

from basemkit.basetest import Basetest

from wmg.cli import WalkMyGraphCmd
from wmg.version import Version
from wmg.webserver import WmgWebserver


class TestCli(Basetest):
    """
    test command line handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.cmd = WalkMyGraphCmd(
            config=WmgWebserver.get_config(), webserver_cls=WmgWebserver
        )

    def run_cmd(self, argv: list) -> str:
        """
        run the command line with the given arguments and return its output
        """
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            self.cmd.cmd_main(argv)
        output = stdout.getvalue()
        return output

    def testVersion(self):
        """
        test the version
        """
        version = Version()
        self.assertEqual("WalkMyGraph", version.name)
        self.assertEqual(version.version, self.cmd.config.version.version)

    def test_tell(self):
        """
        test telling the stories of a walk file
        """
        walk_file = str(WmgWebserver.examples_path() / "scholia-author-q80.yaml")
        output = self.run_cmd(["--tell", walk_file])
        if self.debug:
            print(output)
        self.assertIn("Scholia author aspect walk for Tim Berners-Lee", output)
        self.assertIn("-author of->", output)

    def test_validate(self):
        """
        test validating a walk file as told walks
        """
        walk_file = str(WmgWebserver.examples_path() / "seekcommons.yaml")
        output = self.run_cmd(["--validate", walk_file])
        self.assertIn("5 findings", output)

"""
Created on 2026-11-14

@author: wf
"""

from ngwidgets.webserver_test import WebserverTest

from wmg.cli import WalkMyGraphCmd
from wmg.webserver import WmgWebserver


class TestWmgWebserver(WebserverTest):
    """
    test the WalkMyGraph webserver with the dual view
    see https://github.com/BITPlan/WalkMyGraph/issues/5
    """

    def setUp(self, debug=False, profile=True):
        WebserverTest.setUp(
            self, WmgWebserver, WalkMyGraphCmd, debug=debug, profile=profile
        )

    def test_home(self):
        """
        test that the home page with the dual view answers
        """
        response = self.client.get("/")
        self.assertEqual(200, response.status_code)

    def test_default_walk_set(self):
        """
        test that the Scholia author walk is the default walk
        """
        walk_set = self.ws.get_walk_set()
        self.assertIn("scholia_author_q80", walk_set.walks)

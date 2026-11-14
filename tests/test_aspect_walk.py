"""
Created on 2026-11-14

@author: wf
"""

from basemkit.basetest import Basetest

from wmg.aspect_walk import AspectWalk, AspectWalks
from wmg.webserver import WmgWebserver


class TestAspectWalk(Basetest):
    """
    test the aspect walks: a walk as one line of aspect, query and parameters
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def test_scholia_aspect_walks(self):
        """
        test loading the Scholia aspect walks
        """
        yaml_path = WmgWebserver.examples_path() / "scholia-aspect-walks.yaml"
        aspect_walks = AspectWalks.of_yaml(str(yaml_path))
        if self.debug:
            for walk in aspect_walks.walks:
                print(walk.name, walk.route, walk.min_count, walk.contains)
        self.assertEqual(3, len(aspect_walks.walks))
        by_aspect = aspect_walks.by_aspect()
        self.assertEqual(["author"], list(by_aspect.keys()))
        walk = aspect_walks.walks[2]
        self.assertEqual("author_venue-statistics", walk.name)
        self.assertEqual("/author/venue-statistics/Q2399315", walk.route)
        self.assertEqual(99, walk.min_count)
        self.assertEqual("wikidata:Q976454", walk.contains)

    def test_route(self):
        """
        test the route of single and multi parameter walks
        """
        single = AspectWalk(aspect="work", query="citations", params={"q": "Q1"})
        self.assertEqual("/work/citations/Q1", single.route)
        multi = AspectWalk(
            aspect="organization",
            query="topic",
            params={"q": "Q19375720", "topic": "Q202864"},
        )
        self.assertEqual("/organization/topic?q=Q19375720&topic=Q202864", multi.route)
        none = AspectWalk(aspect="author", query="index")
        self.assertEqual("/author/index", none.route)

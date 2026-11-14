"""
Created on 2026-11-14

@author: wf
"""

from basemkit.basetest import Basetest

from wmg.preview import Previewer
from wmg.walk import Edge, Step, Walk, WalkSet
from wmg.webserver import WmgWebserver


class TestWalk(Basetest):
    """
    test the walk model
    see https://github.com/BITPlan/WalkMyGraph/issues/4
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.examples_path = WmgWebserver.examples_path()

    def load(self, name: str) -> WalkSet:
        """
        load the example walk file with the given name
        """
        walk_set = WalkSet.of_yaml(str(self.examples_path / name))
        return walk_set

    def test_seekcommons(self):
        """
        the navigation_steps.yaml of the Dual View Knowledge Graph Explorer
        loads unchanged: label is the slug, wikidata_id the pid
        """
        walk_set = self.load("seekcommons.yaml")
        self.assertEqual([], walk_set.validate())
        node = walk_set.nodes["seekcommons"]
        self.assertEqual("SeekCommons", node.slug)
        self.assertEqual("wikidata:Q118147033", node.pid)
        self.assertEqual("https://www.wikidata.org/wiki/Q118147033", node.kg_link)
        steps = walk_set.steps("seekcommons_grant_walk")
        self.assertEqual(4, len(steps))
        self.assertEqual("funded by", steps[0].edge_type.label)
        # it is no told walk: no record and no said sentences
        findings = walk_set.validate(told=True)
        if self.debug:
            print(findings)
        self.assertEqual(5, len(findings))

    def test_scholia_author_q80(self):
        """
        the Scholia author walk for Tim Berners-Lee is a valid told walk
        """
        walk_set = self.load("scholia-author-q80.yaml")
        self.assertEqual([], walk_set.validate(told=True))
        node = walk_set.nodes["tim_berners_lee"]
        self.assertEqual("wikidata", node.pid_scheme)
        self.assertEqual("Q80", node.pid_value)
        steps = walk_set.steps("scholia_author_q80")
        self.assertEqual(4, len(steps))
        first = steps[0]
        self.assertEqual("author of", first.edge_type.label)
        self.assertEqual("wikidata:Q29301445", first.to_node.pid)

    def test_tell(self):
        """
        the story of a walk: the said sentences with edge and both nodes
        """
        walk_set = self.load("scholia-author-q80.yaml")
        story = walk_set.tell("scholia_author_q80")
        if self.debug:
            print(story)
        self.assertIn("[Author: Tim Berners-Lee] -author of-> [Work:", story)
        self.assertIn("pid wikidata:Q80", story)
        self.assertEqual(4, story.count("-> ["))

    def test_validate_findings(self):
        """
        unknown nodes, edges and types and unreached nodes are found
        """
        walk_set = self.load("scholia-author-q80.yaml")
        walk_set.nodes["w3c"].type = "unknown_type"
        walk_set.edges["broken"] = Edge(
            from_node="nobody", to_node="w3c", type="unknown_edge_type"
        )
        walk_set.walks["broken_walk"] = Walk(
            label="broken",
            start_node="w3c",
            sequence=[Step(edge="no_such_edge"), Step(edge="tbl_employer_w3c")],
        )
        findings = walk_set.validate()
        if self.debug:
            for finding in findings:
                print(finding)
        text = "\n".join(findings)
        for expected in [
            "node w3c: unknown type unknown_type",
            "edge broken: unknown type unknown_edge_type",
            "edge broken: unknown node nobody",
            "walk broken_walk step 1: unknown edge no_such_edge",
            "which the walk has not reached",
        ]:
            self.assertIn(expected, text)


class TestPreview(Basetest):
    """
    test the previews of the dual view
    see https://github.com/BITPlan/WalkMyGraph/issues/5
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        self.previewer = Previewer()

    def test_embedding_refusal(self):
        """
        a page is shown whole only if the site allows being embedded
        """
        self.assertIsNone(self.previewer.embedding_refusal({"Server": "x"}))
        self.assertIn(
            "X-Frame-Options",
            self.previewer.embedding_refusal({"x-frame-options": "DENY"}),
        )
        self.assertIn(
            "frame-ancestors",
            self.previewer.embedding_refusal(
                {"Content-Security-Policy": "frame-ancestors 'none'"}
            ),
        )

    def test_web_preview_without_url(self):
        """
        a node without web side has nothing to show
        """
        preview = self.previewer.web_preview(None)
        self.assertEqual("none", preview.mode)

    def test_web_preview_unreachable(self):
        """
        a page that can not be read is shown as link
        """
        preview = self.previewer.web_preview("http://127.0.0.1:9/nothing")
        self.assertEqual("link", preview.mode)
        self.assertIn("not read", preview.reason)

    def test_kg_preview(self):
        """
        the kg side is built from data: the PentaLink and for a wikidata
        pid label and description from the abstract endpoint wikidata
        """
        walk_set = WalkSet.of_yaml(
            str(WmgWebserver.examples_path() / "scholia-author-q80.yaml")
        )
        node = walk_set.nodes["tim_berners_lee"]
        preview = self.previewer.kg_preview(node, "Author")
        if self.debug:
            print(preview)
        self.assertEqual("data", preview.mode)
        self.assertEqual("https://www.wikidata.org/wiki/Q80", preview.url)
        self.assertEqual("wikidata:Q80", preview.facts["pid"])
        self.assertEqual("Author", preview.facts["type"])
        if preview.reason:
            self.skipTest(preview.reason)
        self.assertEqual("Tim Berners-Lee", preview.facts["label"])
        self.assertIn("description", preview.facts)

    def test_invalid_wikidata_id(self):
        """
        only Wikidata ids reach the query
        """
        with self.assertRaises(ValueError):
            self.previewer.wikidata_facts("Q80 } #")

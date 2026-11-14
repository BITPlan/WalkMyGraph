"""
Created on 2026-11-14

@author: wf

Walk model of WalkMyGraph
see https://github.com/BITPlan/WalkMyGraph/issues/4

A walk is a sequence of nodes joined by typed edges. A node is identified
by a PentaLink: pid, slug, type, kg_url and web_url,
see https://cr.bitplan.com/index.php/PentaLink
"""

from dataclasses import field
from typing import Any, Dict, List, Optional

import yaml
from basemkit.yamlable import lod_storable


@lod_storable
class NodeType:
    """
    a type of node e.g. author
    """

    label: str
    wikidata_id: Optional[str] = None
    icon: Optional[str] = None


@lod_storable
class EdgeType:
    """
    a type of edge e.g. author of
    """

    label: str
    wikidata_id: Optional[str] = None
    icon: Optional[str] = None


@lod_storable
class Node:
    """
    a node of a walk identified by a PentaLink
    """

    slug: str
    type: str
    pid: Optional[str] = None
    kg_url: Optional[str] = None
    web_url: Optional[str] = None

    WIKIDATA_SCHEME = "wikidata"
    WIKIDATA_URL = "https://www.wikidata.org/wiki/"

    @property
    def pid_scheme(self) -> Optional[str]:
        """
        the scheme of my pid e.g. wikidata for wikidata:Q80
        """
        scheme = None
        if self.pid and ":" in self.pid:
            scheme = self.pid.split(":", 1)[0]
        return scheme

    @property
    def pid_value(self) -> Optional[str]:
        """
        my pid without its scheme e.g. Q80 for wikidata:Q80
        """
        value = self.pid
        if self.pid and ":" in self.pid:
            value = self.pid.split(":", 1)[1]
        return value

    @property
    def kg_link(self) -> Optional[str]:
        """
        the url of the knowledge graph side: my kg_url or the Wikidata
        item of a wikidata pid
        """
        link = self.kg_url
        if link is None and self.pid_scheme == self.WIKIDATA_SCHEME:
            link = f"{self.WIKIDATA_URL}{self.pid_value}"
        return link


@lod_storable
class Edge:
    """
    a typed edge between two nodes
    """

    from_node: str
    to_node: str
    type: str


@lod_storable
class Step:
    """
    a step of a walk: the edge taken and the sentence the actor said
    """

    edge: str
    said: Optional[str] = None
    url: Optional[str] = None


@lod_storable
class Walk:
    """
    a walk: a start node and a sequence of steps
    """

    label: str
    start_node: str
    sequence: List[Step] = field(default_factory=list)
    record: Optional[str] = None


@lod_storable
class WalkStep:
    """
    a resolved step of a walk with its nodes, edge and types
    """

    pos: int
    step: Step
    edge: Edge
    edge_type: EdgeType
    from_node: Node
    to_node: Node


@lod_storable
class WalkSet:
    """
    node types, edge types, nodes, edges and walks of a walk file
    """

    node_types: Dict[str, NodeType] = field(default_factory=dict)
    edge_types: Dict[str, EdgeType] = field(default_factory=dict)
    nodes: Dict[str, Node] = field(default_factory=dict)
    edges: Dict[str, Edge] = field(default_factory=dict)
    walks: Dict[str, Walk] = field(default_factory=dict)

    @classmethod
    def normalize(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        normalize the record of a walk file so that the navigation_steps.yaml
        of the Dual View Knowledge Graph Explorer loads unchanged:
        label is accepted as slug and wikidata_id as pid of a node,
        from and to are the yaml keys of from_node and to_node of an edge

        Args:
            record: the record as read from yaml

        Returns:
            the normalized record
        """
        known_node_keys = {"slug", "type", "pid", "kg_url", "web_url"}
        nodes = {}
        for key, node in (record.get("nodes") or {}).items():
            node = dict(node)
            if "slug" not in node and "label" in node:
                node["slug"] = node["label"]
            if "pid" not in node and "wikidata_id" in node:
                node["pid"] = f"{Node.WIKIDATA_SCHEME}:{node['wikidata_id']}"
            nodes[key] = {k: v for k, v in node.items() if k in known_node_keys}
        edges = {}
        for key, edge in (record.get("edges") or {}).items():
            edges[key] = {
                "from_node": edge.get("from", edge.get("from_node")),
                "to_node": edge.get("to", edge.get("to_node")),
                "type": edge.get("type"),
            }
        normalized = {
            "node_types": record.get("node_types") or {},
            "edge_types": record.get("edge_types") or {},
            "nodes": nodes,
            "edges": edges,
            "walks": record.get("walks") or {},
        }
        return normalized

    @classmethod
    def of_yaml(cls, yaml_path: str) -> "WalkSet":
        """
        load a walk set from the given walk file

        Args:
            yaml_path: the path of the yaml file
        """
        with open(yaml_path, "r", encoding="utf-8") as yaml_file:
            record = yaml.safe_load(yaml_file)
        walk_set = cls.from_dict(cls.normalize(record))
        return walk_set

    def validate(self, told: bool = False) -> List[str]:
        """
        validate my structure

        Args:
            told: if True also check what a told walk needs: a record per
                walk and a said sentence per step

        Returns:
            the list of findings - empty if I am valid
        """
        findings: List[str] = []
        slugs: Dict[str, str] = {}
        for key, node in self.nodes.items():
            if node.type not in self.node_types:
                findings.append(f"node {key}: unknown type {node.type}")
            slug_key = f"{node.type}/{node.slug}"
            if slug_key in slugs:
                findings.append(
                    f"node {key}: slug {node.slug} of type {node.type} "
                    f"also used by node {slugs[slug_key]}"
                )
            slugs[slug_key] = key
        for key, edge in self.edges.items():
            if edge.type not in self.edge_types:
                findings.append(f"edge {key}: unknown type {edge.type}")
            for node_key in [edge.from_node, edge.to_node]:
                if node_key not in self.nodes:
                    findings.append(f"edge {key}: unknown node {node_key}")
        for key, walk in self.walks.items():
            findings.extend(self.validate_walk(key, walk, told))
        return findings

    def validate_walk(self, key: str, walk: Walk, told: bool) -> List[str]:
        """
        validate the given walk: its start node and edges are known and
        every edge starts at a node the walk has reached before

        Args:
            key: the key of the walk
            walk: the walk
            told: if True check record and said sentences
        """
        findings: List[str] = []
        if walk.start_node not in self.nodes:
            findings.append(f"walk {key}: unknown start node {walk.start_node}")
        if told and not walk.record:
            findings.append(f"walk {key}: no record")
        reached = {walk.start_node}
        for index, step in enumerate(walk.sequence):
            pos = index + 1
            edge = self.edges.get(step.edge)
            if edge is None:
                findings.append(f"walk {key} step {pos}: unknown edge {step.edge}")
                continue
            if edge.from_node not in reached:
                findings.append(
                    f"walk {key} step {pos}: edge {step.edge} starts at "
                    f"{edge.from_node} which the walk has not reached"
                )
            reached.add(edge.to_node)
            if told and not step.said:
                findings.append(f"walk {key} step {pos}: no said sentence")
        return findings

    def steps(self, walk_key: str) -> List[WalkStep]:
        """
        get the resolved steps of the given walk

        Args:
            walk_key: the key of the walk

        Raises:
            KeyError: if the walk, an edge, a node or an edge type is unknown
        """
        walk = self.walks[walk_key]
        walk_steps: List[WalkStep] = []
        for index, step in enumerate(walk.sequence):
            edge = self.edges[step.edge]
            walk_step = WalkStep(
                pos=index + 1,
                step=step,
                edge=edge,
                edge_type=self.edge_types[edge.type],
                from_node=self.nodes[edge.from_node],
                to_node=self.nodes[edge.to_node],
            )
            walk_steps.append(walk_step)
        return walk_steps

    def tell(self, walk_key: str) -> str:
        """
        tell the story of the given walk: the said sentences in order, each
        followed by the edge with type, slug and both sides of its nodes

        Args:
            walk_key: the key of the walk
        """
        walk = self.walks[walk_key]
        lines = [f"{walk.label}"]
        if walk.record:
            lines.append(f"record: {walk.record}")
        for walk_step in self.steps(walk_key):
            said = walk_step.step.said or f"{walk_step.pos}."
            lines.append("")
            lines.append(said)
            lines.append(
                f"  {self.node_text(walk_step.from_node)} "
                f"-{walk_step.edge_type.label}-> "
                f"{self.node_text(walk_step.to_node)}"
            )
            for node in [walk_step.from_node, walk_step.to_node]:
                lines.append(f"  {node.slug}: pid {node.pid}")
                lines.append(f"    kg:  {node.kg_link}")
                lines.append(f"    web: {node.web_url}")
        text = "\n".join(lines)
        return text

    def node_text(self, node: Node) -> str:
        """
        get the short text of the given node: the label of its type and its slug
        """
        node_type = self.node_types.get(node.type)
        type_label = node_type.label if node_type else node.type
        text = f"[{type_label}: {node.slug}]"
        return text

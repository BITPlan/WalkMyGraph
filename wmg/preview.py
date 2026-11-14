"""
Created on 2026-11-14

@author: wf

Preview of the two sides of a node in the dual view
see https://github.com/BITPlan/WalkMyGraph/issues/5

A dual view is two links with a preview each. The preview is made from
content that was read on the step, so that rules can decide what is shown.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import requests
from lodstorage.prefix_config import PrefixConfigs
from lodstorage.query import EndpointManager, Query
from lodstorage.sparql import SPARQL

from wmg.version import Version
from wmg.walk import Node


@dataclass
class Preview:
    """
    the preview of one side of a node
    """

    url: Optional[str] = None
    title: Optional[str] = None
    # whole: show the page itself, link: show the link with its title,
    # data: show facts built from data, none: nothing to show
    mode: str = "none"
    facts: Dict[str, str] = field(default_factory=dict)
    reason: Optional[str] = None


class Previewer:
    """
    responsible for the previews of the dual view: reads the target and
    decides by rules how it is shown

    the rules so far:
    - web side: the whole page is shown if the site allows being embedded,
      else the link with the title that was read
    - kg side: built from data - the PentaLink of the node and, for a
      wikidata pid, label and description from the abstract endpoint wikidata
    """

    USER_AGENT = (
        f"WalkMyGraph/{Version.version} "
        "(https://github.com/BITPlan/WalkMyGraph) python-requests"
    )
    TITLE_PATTERN = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
    WIKIDATA_ID_PATTERN = re.compile(r"^[QPL][0-9]+$")
    # the abstract endpoint name - resolved by the endpoint layers of pyLoDStorage
    ENDPOINT_NAME = "wikidata"
    WIKIDATA_QUERY = """SELECT ?label ?description WHERE {
  OPTIONAL { wd:%s rdfs:label ?label . FILTER(LANG(?label) = "en") }
  OPTIONAL { wd:%s schema:description ?description . FILTER(LANG(?description) = "en") }
}"""

    def __init__(self, timeout: float = 5.0, endpoint_name: Optional[str] = None):
        """
        constructor

        Args:
            timeout: seconds to wait when reading a target
            endpoint_name: the endpoint for the kg side - default: wikidata
        """
        self.timeout = timeout
        self.endpoint_name = endpoint_name or self.ENDPOINT_NAME

    def embedding_refusal(self, headers: Dict[str, str]) -> Optional[str]:
        """
        get the reason why a page refuses to be embedded

        Args:
            headers: the response headers of the page

        Returns:
            the refusing header or None if the page allows being embedded
        """
        refusal = None
        lower = {key.lower(): value for key, value in headers.items()}
        frame_options = lower.get("x-frame-options")
        csp = lower.get("content-security-policy", "")
        if frame_options:
            refusal = f"X-Frame-Options: {frame_options}"
        elif "frame-ancestors" in csp.lower():
            refusal = "Content-Security-Policy: frame-ancestors"
        return refusal

    def web_preview(self, url: Optional[str]) -> Preview:
        """
        read the web side and decide how it is shown

        Args:
            url: the web_url of the node
        """
        preview = Preview(url=url)
        if not url:
            preview.reason = "no web_url"
            return preview
        try:
            response = requests.get(
                url,
                headers={"User-Agent": self.USER_AGENT},
                timeout=self.timeout,
            )
        except requests.RequestException as ex:
            preview.mode = "link"
            preview.reason = f"not read: {type(ex).__name__}"
            return preview
        match = self.TITLE_PATTERN.search(response.text or "")
        if match:
            preview.title = re.sub(r"\s+", " ", match.group(1)).strip()
        refusal = self.embedding_refusal(response.headers)
        if response.status_code != 200:
            preview.mode = "link"
            preview.reason = f"HTTP {response.status_code}"
        elif refusal:
            preview.mode = "link"
            preview.reason = refusal
        else:
            preview.mode = "whole"
        return preview

    def wikidata_facts(self, qid: str) -> Dict[str, str]:
        """
        get label and description of a Wikidata entity from the endpoint

        Args:
            qid: the Wikidata id e.g. Q80

        Raises:
            ValueError: if the id is no Wikidata id or the endpoint is unknown
        """
        if not self.WIKIDATA_ID_PATTERN.match(qid):
            raise ValueError(f"invalid Wikidata id {qid}")
        endpoints = EndpointManager.getEndpoints(lang="sparql")
        endpoint = endpoints.get(self.endpoint_name)
        if endpoint is None:
            raise ValueError(f"unknown endpoint {self.endpoint_name}")
        query = Query(
            name="WikidataFacts",
            query=self.WIKIDATA_QUERY % (qid, qid),
            lang="sparql",
            endpoint=endpoint.endpoint,
        )
        query.add_endpoint_prefixes(endpoint, PrefixConfigs.get_instance())
        sparql = SPARQL(endpoint.endpoint, agent=self.USER_AGENT)
        rows: List[Dict[str, str]] = sparql.queryAsListOfDicts(query.query)
        facts: Dict[str, str] = {}
        if rows:
            for key in ["label", "description"]:
                value = rows[0].get(key)
                if value:
                    facts[key] = str(value)
        return facts

    def kg_preview(self, node: Node, type_label: Optional[str] = None) -> Preview:
        """
        build the kg side of the given node from data

        Args:
            node: the node
            type_label: the label of the type of the node
        """
        preview = Preview(url=node.kg_link, title=node.slug, mode="data")
        preview.facts["type"] = type_label or node.type
        preview.facts["slug"] = node.slug
        if node.pid:
            preview.facts["pid"] = node.pid
        if node.pid_scheme == Node.WIKIDATA_SCHEME:
            try:
                preview.facts.update(self.wikidata_facts(node.pid_value))
            except Exception as ex:
                preview.reason = f"no data from {self.endpoint_name}: {ex}"
        return preview

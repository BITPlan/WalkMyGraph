"""
Created on 2026-11-14

@author: wf

Aspect walks: a walk given as one line - aspect, query and parameters
see https://github.com/WolfgangFahl/nicescholia/issues/15

An aspect is a node type, the query walks one edge type from a node of
that type, the parameters name the start node. The result of the query
is what the walk reaches; the expected result can falsify the walk,
not verify it.
"""

from dataclasses import field
from typing import Dict, List, Optional

from basemkit.yamlable import lod_storable


@lod_storable
class AspectWalk:
    """
    a walk as one line: aspect, query and parameters with its expected result
    """

    aspect: str
    query: str
    params: Dict[str, str] = field(default_factory=dict)
    # expected result: a lower bound of the number of entries and the pid
    # of one entry that must be among them
    min_count: Optional[int] = None
    contains: Optional[str] = None
    # where the example comes from, e.g. a row of an examples sheet
    source: Optional[str] = None

    @property
    def name(self) -> str:
        """
        the name of the named parameterized query: <aspect>_<query>
        """
        name = f"{self.aspect}_{self.query}"
        return name

    @property
    def route(self) -> str:
        """
        the route of the single view of this walk: /<aspect>/<query>/<q>
        for a single parameter q, else /<aspect>/<query> with the
        parameters as query string
        """
        route = f"/{self.aspect}/{self.query}"
        if list(self.params.keys()) == ["q"]:
            route = f"{route}/{self.params['q']}"
        elif self.params:
            query_string = "&".join(
                f"{key}={value}" for key, value in self.params.items()
            )
            route = f"{route}?{query_string}"
        return route


@lod_storable
class AspectWalks:
    """
    a list of aspect walks
    """

    walks: List[AspectWalk] = field(default_factory=list)

    @classmethod
    def of_yaml(cls, yaml_path: str) -> "AspectWalks":
        """
        load the aspect walks from the given yaml file

        Args:
            yaml_path: the path of the yaml file
        """
        aspect_walks = cls.load_from_yaml_file(yaml_path)
        return aspect_walks

    def by_aspect(self) -> Dict[str, List[AspectWalk]]:
        """
        get my walks by aspect
        """
        by_aspect: Dict[str, List[AspectWalk]] = {}
        for walk in self.walks:
            by_aspect.setdefault(walk.aspect, []).append(walk)
        return by_aspect

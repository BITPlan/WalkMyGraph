"""
Created on 2026-11-14

@author: wf

Webserver of WalkMyGraph
see https://github.com/BITPlan/WalkMyGraph/issues/5
"""

from pathlib import Path
from typing import Optional

from ngwidgets.input_webserver import InputWebserver, InputWebSolution, WebserverConfig
from nicegui import Client

from wmg.dualview import DualView
from wmg.version import Version
from wmg.walk import WalkSet


class WmgWebserver(InputWebserver):
    """
    the WalkMyGraph webserver
    """

    @classmethod
    def get_config(cls) -> WebserverConfig:
        config = WebserverConfig(
            short_name="wmg",
            timeout=6.0,
            copy_right="(c) 2026 Wolfgang Fahl",
            version=Version(),
            default_port=9881,
        )
        server_config = WebserverConfig.get(config)
        server_config.solution_class = WmgSolution
        return server_config

    def __init__(self):
        super().__init__(config=WmgWebserver.get_config())
        self.walk_set: Optional[WalkSet] = None

    @classmethod
    def examples_path(cls) -> Path:
        """
        get the path of the example walks
        """
        path = Path(__file__).parent.parent / "wmg_examples"
        return path

    def get_walk_set(self) -> WalkSet:
        """
        get the walks to show: the walk file given as input or the
        Scholia author walk of the examples
        """
        if self.walk_set is None:
            yaml_path = getattr(getattr(self, "args", None), "input", None)
            if not yaml_path:
                yaml_path = self.examples_path() / "scholia-author-q80.yaml"
            self.walk_set = WalkSet.of_yaml(str(yaml_path))
        return self.walk_set


class WmgSolution(InputWebSolution):
    """
    the WalkMyGraph solution per client
    """

    def __init__(self, webserver: WmgWebserver, client: Client):
        super().__init__(webserver, client)
        self.dual_view = None

    async def home(self):
        """
        the home page: the dual view of the walks
        """

        def show():
            self.dual_view = DualView(self, self.webserver.get_walk_set())
            self.dual_view.setup_ui()

        await self.setup_content_div(show)
        # both sides of the first node are read and shown once the client is
        # connected - before that the client may be gone again while reading
        await self.client.connected()
        await self.dual_view.show_step()

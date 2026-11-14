"""
Created on 2026-11-14

@author: wf

Dual view of a walk with ngwidgets and NiceGUI
see https://github.com/BITPlan/WalkMyGraph/issues/5
"""

from typing import List, Optional

from nicegui import run, ui

from wmg.preview import Preview, Previewer
from wmg.walk import Node, WalkSet, WalkStep


class DualView:
    """
    steps through a walk and shows for the node reached two links with a
    preview each: the knowledge graph side and the web side
    """

    def __init__(self, solution, walk_set: WalkSet, previewer: Previewer = None):
        """
        constructor

        Args:
            solution: the web solution to show the dual view in
            walk_set: the walks to show
            previewer: the previewer - created if not given
        """
        self.solution = solution
        self.walk_set = walk_set
        self.previewer = previewer if previewer else Previewer()
        self.walk_key: Optional[str] = None
        self.walk_steps: List[WalkStep] = []
        # position 0 is the start node, position n the node step n reaches
        self.pos = 0
        self.pos_label = None
        self.story = None
        self.kg_card = None
        self.web_card = None

    def setup_ui(self):
        """
        setup the user interface
        """
        walk_keys = list(self.walk_set.walks.keys())
        options = {key: self.walk_set.walks[key].label for key in walk_keys}
        with ui.row().classes("w-full items-center"):
            self.walk_select = ui.select(
                options=options,
                label="Walk",
                value=walk_keys[0] if walk_keys else None,
                on_change=self.on_walk_change,
            ).classes("w-96")
            ui.button(icon="navigate_before", on_click=self.on_prev).props("outline")
            self.pos_label = ui.label("").classes("text-sm")
            ui.button(icon="navigate_next", on_click=self.on_next).props("outline")
        self.story = ui.column().classes("w-full")
        with ui.row().classes("w-full no-wrap items-stretch"):
            self.kg_card = ui.card().classes("w-1/2")
            self.web_card = ui.card().classes("w-1/2")
        if walk_keys:
            self.select_walk(walk_keys[0])
            # the first step is read and shown once the client is connected -
            # a client that is not connected yet may be gone before the
            # reading of both sides is done
            ui.context.client.on_connect(self.show_step)

    def select_walk(self, walk_key: str):
        """
        select the given walk and show its start node

        Args:
            walk_key: the key of the walk
        """
        self.walk_key = walk_key
        self.walk_steps = self.walk_set.steps(walk_key)
        self.pos = 0

    async def on_walk_change(self, event):
        """
        react on the selection of a walk
        """
        self.select_walk(event.value)
        await self.show_step()

    async def on_prev(self):
        """
        go to the previous step
        """
        if self.pos > 0:
            self.pos -= 1
            await self.show_step()

    async def on_next(self):
        """
        go to the next step
        """
        if self.pos < len(self.walk_steps):
            self.pos += 1
            await self.show_step()

    def current_node(self) -> Node:
        """
        get the node of the current position
        """
        if self.pos == 0:
            walk = self.walk_set.walks[self.walk_key]
            node = self.walk_set.nodes[walk.start_node]
        else:
            node = self.walk_steps[self.pos - 1].to_node
        return node

    async def show_step(self):
        """
        show the current step: read both sides of its node and show them
        """
        try:
            node = self.current_node()
            self.show_story()
            node_type = self.walk_set.node_types.get(node.type)
            type_label = node_type.label if node_type else node.type
            kg_preview = await run.io_bound(self.previewer.kg_preview, node, type_label)
            web_preview = await run.io_bound(self.previewer.web_preview, node.web_url)
            self.show_preview(self.kg_card, "Knowledge graph", kg_preview)
            self.show_preview(self.web_card, "Web", web_preview)
        except Exception as ex:
            self.solution.handle_exception(ex)

    def show_story(self):
        """
        show the position, the said sentence and the edge of the current step
        """
        self.pos_label.set_text(f"{self.pos} of {len(self.walk_steps)}")
        self.story.clear()
        with self.story:
            if self.pos == 0:
                node = self.current_node()
                ui.label(f"Start: {self.walk_set.node_text(node)}").classes(
                    "text-lg font-bold"
                )
            else:
                walk_step = self.walk_steps[self.pos - 1]
                if walk_step.step.said:
                    ui.label(walk_step.step.said).classes("text-lg")
                ui.label(
                    f"{self.walk_set.node_text(walk_step.from_node)} "
                    f"-{walk_step.edge_type.label}-> "
                    f"{self.walk_set.node_text(walk_step.to_node)}"
                ).classes("font-bold")

    def show_preview(self, card, side: str, preview: Preview):
        """
        show the given preview: its link and what the previewer decided

        Args:
            card: the card to show the preview in
            side: the name of the side
            preview: the preview
        """
        card.clear()
        with card:
            ui.label(side).classes("text-sm text-gray-500")
            if preview.url:
                ui.link(
                    preview.title or preview.url, preview.url, new_tab=True
                ).classes("text-lg")
            if preview.mode == "data":
                with ui.grid(columns=2).classes("gap-x-4 gap-y-1"):
                    for key, value in preview.facts.items():
                        ui.label(key).classes("text-gray-500")
                        ui.label(value)
            elif preview.mode == "whole":
                ui.element("iframe").props(f'src="{preview.url}"').classes(
                    "w-full"
                ).style("height: 60vh; border: 1px solid #ddd")
            if preview.reason:
                ui.label(preview.reason).classes("text-sm text-gray-500")

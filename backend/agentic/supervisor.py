# backend/agentic/nodes/supervisor_node.py

import logging
from backend.agentic.state import HeliconState

logger = logging.getLogger("Supervisor")
logging.basicConfig(level=logging.INFO)

class SupervisorNode:
    """
    Dynamic Router for Helicon Multi-Agent Workflow.
    """

    def run(self, state: HeliconState) -> HeliconState:
        next_step = self.decide_next(state)
        state.next_node = next_step
        state.log("supervisor", {"next_node": next_step})
        return state

    # -----------------------------------------------------
    def decide_next(self, state: HeliconState):

        # 1) Intent first
        if state.intent is None:
            return "intent"

        # 2) Entity extraction
        if not state.entities:
            return "entity"

        # 3) Vision check
        need_vision = False

        if state.image_path and state.vision_data is None:
            need_vision = True

        vision_keywords = ["image", "figure", "plot", "chart", "gel", "microscopy"]
        if any(k in state.question.lower() for k in vision_keywords):
            if state.vision_data is None:
                need_vision = True

        if need_vision:
            return "vision"

        # 4) Graph search
        if state.graph_result is None:
            return "graph"

        # 5) Evidence
        if state.evidence_paths is None:
            return "evidence"

        # 6) Web crawling
        if state.crawler_data is None:
            return "crawler"

        # 7) Protein design
        if state.intent == "protein_design" and state.design_result is None:
            return "design"

        # 8) Structure prediction
        if state.design_result and state.structure_result is None:
            return "structure"

        # 9) Render 3D
        if state.structure_result and state.structure_image is None:
            return "render"

        # 10) Reasoning aggregation
        if state.reasoning_summary is None:
            return "reason"

        # 11) Final
        return "final"



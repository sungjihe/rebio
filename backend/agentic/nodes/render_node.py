# backend/agentic/nodes/render_node.py

import logging
from backend.agentic.state import HeliconState

logger = logging.getLogger("RenderNode")
logging.basicConfig(level=logging.INFO)


class RenderNode:
    """
    RenderNode
    -----------
    This node does NOT create PNG files.
    It simply forwards the PDB text from StructureNode.

    Streamlit / frontend will handle py3Dmol or NGL Viewer rendering.
    """

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[RenderNode] Running render step...")

        if not state.structure_result:
            logger.warning("[RenderNode] No structure_result found.")
            return state

        # No image generation here
        state.structure_image = None

        state.log("render_node", {"success": True})
        return state

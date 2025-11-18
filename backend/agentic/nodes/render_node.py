# backend/agentic/nodes/render_node.py

import logging
from backend.agentic.state import HeliconState

logger = logging.getLogger("RenderNode")
logging.basicConfig(level=logging.INFO)


class RenderNode:

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[RenderNode] Passing ESMFold PDB text through...")

        if not state.structure_result:
            logger.warning("[RenderNode] No structure_result found.")
            return state

        pdb_text = state.structure_result.get("pdb_text")

        if pdb_text:
            # Streamlit에서 직접 py3Dmol로 렌더 가능하므로 저장 불필요
            state.structure_result["pdb_text"] = pdb_text

       state.log("render_node", {"success": True})
        return state

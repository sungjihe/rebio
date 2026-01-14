# backend/agentic/nodes/render_node.py

import logging
from backend.agentic.state import HeliconState

logger = logging.getLogger("RenderNode")
logging.basicConfig(level=logging.INFO)


class RenderNode:
    """
    RenderNode: structure_result(PDB text)를 프론트로 전달만 함.
    PNG 생성 없음. Streamlit에서 py3Dmol/NGL로 렌더링.
    """

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[RenderNode] Running render step...")

        # 렌더 결과 이미지 생성은 하지 않음 (명시적으로 None)
        state.structure_image = None

        # ✅ RenderNode가 실행되었음을 표시 (루프 가드/상태 머신에서 사용)
        state.render_done = True

        if not state.structure_result:
            logger.warning("[RenderNode] No structure_result found.")
            state.log("render_node", {"success": False, "reason": "no_structure_result"})
            return state

        state.log("render_node", {"success": True})
        return state

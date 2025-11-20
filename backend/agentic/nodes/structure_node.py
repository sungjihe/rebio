# backend/agentic/nodes/structure_node.py

import logging
from backend.agentic.state import HeliconState
from backend.agentic.esmfold_model import ESMFoldPredictor

logger = logging.getLogger("StructureNode")
logging.basicConfig(level=logging.INFO)

# ---------------------------------------------------
# Global Model Cache (ESMFold는 heavy model이므로 global로)
# ---------------------------------------------------
_ESMFOLD_MODEL = None


def load_esmfold_once():
    """Load ESMFold only once globally."""
    global _ESMFOLD_MODEL
    if _ESMFOLD_MODEL is None:
        logger.info("[StructureNode] Loading ESMFold model (lazy)...")
        _ESMFOLD_MODEL = ESMFoldPredictor()
    return _ESMFOLD_MODEL


class StructureNode:
    """
    Protein Structure Prediction using ESMFold (Lazy-loading version)
    """

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[StructureNode] Running structure prediction...")

        seq = None

        # ------------------------------------------------------------------
        # 1) Use redesigned variant (best-scoring)
        # ------------------------------------------------------------------
        redesigned = state.designed_protein
        if redesigned:
            if isinstance(designed := redesigned[0], dict):
                seq = designed.get("sequence")

        # ------------------------------------------------------------------
        # 2) Fallback to user-provided raw sequence
        # ------------------------------------------------------------------
        if not seq:
            seq = state.entities.get("protein_sequence")

        # ------------------------------------------------------------------
        # 3) Validate
        # ------------------------------------------------------------------
        if not seq or len(seq) < 20:
            logger.warning("[StructureNode] No valid sequence for structure prediction.")
            state.structure_result = {
                "ok": False,
                "error": "invalid_sequence",
                "length": len(seq) if seq else 0,
            }
            state.structure_path = None
            return state

        # ------------------------------------------------------------------
        # 4) Load model lazily
        # ------------------------------------------------------------------
        model = load_esmfold_once()

        # ------------------------------------------------------------------
        # 5) Predict structure (PDB text)
        # ------------------------------------------------------------------
        try:
            pdb_text = model.predict_pdb(seq)
        except Exception as e:
            logger.error(f"[StructureNode] ESMFold failed: {e}")
            state.structure_result = {
                "ok": False,
                "error": str(e),
            }
            state.structure_path = None
            return state

        # ------------------------------------------------------------------
        # 6) Save to state (no file I/O)
        # ------------------------------------------------------------------
        state.structure_result = {
            "ok": True,
            "sequence": seq,
            "pdb_text": pdb_text,
        }

        state.structure_path = None
        state.structure_image = None  # RenderNode will handle image later

        state.log("structure_node", {
            "sequence_length": len(seq),
        })

        return state

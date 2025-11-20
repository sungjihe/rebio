# backend/agentic/nodes/structure_node.py

import logging
from backend.agentic.state import HeliconState
from backend.agentic.esmfold_model import ESMFoldPredictor

logger = logging.getLogger("StructureNode")
logging.basicConfig(level=logging.INFO)


class StructureNode:
    """
    Protein Structure Prediction using ESMFold
    """

    def __init__(self):
        self.model = ESMFoldPredictor()

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[StructureNode] Running ESMFold structure prediction...")

        seq = None

        # ---------------------------------------
        # 1) Use redesigned variant (best-scoring)
        # ---------------------------------------
        if state.designed_protein and isinstance(state.designed_protein, list):
            first = state.designed_protein[0]
            seq = first.get("sequence")

        # ---------------------------------------
        # 2) Else fall back to user-provided sequence
        # ---------------------------------------
        if not seq:
            seq = state.entities.get("protein_sequence")

        # ---------------------------------------
        # 3) Validate sequence
        # ---------------------------------------
        if not seq or len(seq) < 20:
            logger.warning("[StructureNode] No valid sequence for structure prediction.")
            state.structure_result = None
            state.structure_path = None
            return state

        # ---------------------------------------
        # 4) Predict PDB using ESMFold
        # ---------------------------------------
        pdb_text = self.model.predict_pdb(seq)

        # ---------------------------------------
        # 5) Store in state (no file I/O)
        # ---------------------------------------
        state.structure_result = {
            "sequence": seq,
            "pdb_text": pdb_text,
        }

        state.structure_path = None  # no file
        state.structure_image = None  # handled by RenderNode later

        state.log("structure_node", {
            "sequence": seq,
            "length": len(seq),
        })

        return state

# backend/agentic/nodes/structure_node.py

import logging
from backend.agentic.state import HeliconState
from backend.agentic.esmfold_model import ESMFoldPredictor


logger = logging.getLogger("StructureNode")
logging.basicConfig(level=logging.INFO)


class StructureNode:
    """
    Protein Structure Prediction using ESMFold (local GPU)
    - Takes sequence from state.entities or design_result
    - Produces PDB text output
    - Stores structure_result with pdb_text
    """

    def __init__(self):
        self.model = ESMFoldPredictor()

    def run(self, state: HeliconState) -> HeliconState:

        logger.info("[StructureNode] Running ESMFold structure prediction...")

        # 1) Sequence extraction
        seq = None

        # 단백질 재설계가 존재하면 변이된 서열 사용
        if state.design_result:
            seq = state.design_result.get("best_sequence")

        # 아니면 유저 입력(sequence)
        if not seq:
            seq = state.entities.get("sequence") or state.question

        if not seq or len(seq) < 20:
            logger.warning("[StructureNode] Invalid or missing sequence.")
            state.structure_result = None
            return state

        # 2) Run ESMFold
        pdb_text = self.model.predict_pdb(seq)

        # 3) Save results to state
        state.structure_result = {
            "sequence": seq,
            "pdb_text": pdb_text,
        }

       state.log("structure_node", {"sequence": seq, "length": len(seq)})

        return state

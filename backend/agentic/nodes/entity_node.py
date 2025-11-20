# backend/agentic/nodes/entity_node.py

import json
import logging
from typing import Dict, Any

from backend.agentic.state import HeliconState
from backend.agent.vision_reasoner import VisionReasoner

logger = logging.getLogger("EntityNode")
logging.basicConfig(level=logging.INFO)


class EntityNode:
    """
    EntityNode v2 (TherapeuticProtein 기반)
    - uniprot_id (protein or therapeutic protein)
    - disease_id
    - protein_sequence
    - image_path

    ❌ drugbank_id 제거됨
    """

    def __init__(self):
        # VisionReasoner(text-only도 지원)
        self.llm = VisionReasoner()

    # ---------------------------------------------------------
    # 실행
    # ---------------------------------------------------------
    def run(self, state: HeliconState) -> HeliconState:

        question = state.question

        prompt = f"""
Extract biological entities from the user question.
Return ONLY a valid JSON object — no explanation.

Extract and fill the following keys:
- uniprot_id: protein ID or therapeutic protein UniProt ID
- disease_id: any disease name / identifier
- protein_sequence: amino-acid sequence (ACDEFGHIKLMNPQRSTVWY)
- image_path: if the question references an image

Rules:
- If a value is not found, return null.
- protein_sequence must be uppercase, AA-only.
- uniprot_id must be uppercase.
- Return ONLY one JSON object.

User question:
{question}

Return JSON:
{{
  "uniprot_id": null,
  "disease_id": null,
  "protein_sequence": null,
  "image_path": null
}}
"""

        # LLM 호출
        response = self.llm.reason(prompt)
        raw = response["answer"]

        # JSON decode
        try:
            data = json.loads(raw)
        except Exception:
            logger.error("[EntityNode] JSON Parse Error. Using fallback.")
            data = {}

        # Default keys
        for key in ["uniprot_id", "disease_id", "protein_sequence", "image_path"]:
            data.setdefault(key, None)

        # Normalize uniprot_id
        if isinstance(data.get("uniprot_id"), str):
            data["uniprot_id"] = data["uniprot_id"].strip().upper()

        # Validate protein sequence
        seq = data.get("protein_sequence")
        if isinstance(seq, str):
            seq_clean = seq.replace(" ", "").strip().upper()
            valid_set = set("ACDEFGHIKLMNPQRSTVWY")
            if all(aa in valid_set for aa in seq_clean):
                data["protein_sequence"] = seq_clean
            else:
                logger.warning("[EntityNode] Invalid amino acids removed → sequence reset.")
                data["protein_sequence"] = None

        # Save to state
        state.entities = data
        state.log("entity_node", data)

        logger.info(f"[EntityNode] Extracted entities: {data}")
        return state


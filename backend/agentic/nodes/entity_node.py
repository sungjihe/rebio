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
    질문에서 엔티티를 추출하는 Multi-Agent 노드.
    uniprot_id / disease_id / drugbank_id / protein_sequence / image_path 등을 식별한다.
    """

    def __init__(self):
        self.llm = VisionReasoner()  # 텍스트-only도 지원

    # ─────────────────────────────────────────────
    # 실행 함수
    # ─────────────────────────────────────────────
    def run(self, state: HeliconState) -> HeliconState:

        question = state.question

        prompt = f"""
Extract biological entities from the user's question.  
Return ONLY a valid JSON object — no explanation.

Keys to extract:
- uniprot_id (string or null)
- disease_id (string or null)
- drugbank_id (string or null)
- protein_sequence (AA sequence or null)
- image_path (string or null)

Rules:
- If nothing is found, return null for that field.
- Ensure protein_sequence is uppercase and contains ONLY valid amino acids (ACDEFGHIKLMNPQRSTVWY).
- Clean whitespace.
- Only one JSON object must be returned.

User question:
{question}

Return JSON:
{{
    "uniprot_id": null,
    "disease_id": null,
    "drugbank_id": null,
    "protein_sequence": null,
    "image_path": null
}}
"""

        # VisionReasoner 대신 텍스트-only 모드
        response = self.llm.reason(prompt)
        raw = response["answer"]

        try:
            data = json.loads(raw)
        except Exception:
            logger.error("[EntityNode] JSON Parse Error. Using fallback.")
            data = {}

        # 기본값 보장
        for key in ["uniprot_id", "disease_id", "drugbank_id", "protein_sequence", "image_path"]:
            data.setdefault(key, None)

        # Clean-up and normalization
        if isinstance(data.get("uniprot_id"), str):
            data["uniprot_id"] = data["uniprot_id"].strip().upper()

        if isinstance(data.get("drugbank_id"), str):
            data["drugbank_id"] = data["drugbank_id"].strip().upper()

        # Validate protein sequence
        seq = data.get("protein_sequence")
        if isinstance(seq, str):
            seq_clean = seq.replace(" ", "").upper()
            valid_set = set("ACDEFGHIKLMNPQRSTVWY")
            if all(aa in valid_set for aa in seq_clean):
                data["protein_sequence"] = seq_clean
            else:
                logger.warning("[EntityNode] Invalid AA detected. Resetting sequence.")
                data["protein_sequence"] = None

        state.entities = data
        state.log("entity_node", data)

        logger.info(f"[EntityNode] Extracted entities: {data}")
        return state

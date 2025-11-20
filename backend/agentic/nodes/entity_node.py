# backend/agentic/nodes/entity_node.py

import json
import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI

from backend.agentic.state import HeliconState

load_dotenv()

logger = logging.getLogger("EntityNode")
logging.basicConfig(level=logging.INFO)


class EntityNode:
    """
    EntityNode v2 (TherapeuticProtein 기반)
    - uniprot_id (protein or therapeutic protein)
    - disease_id
    - protein_sequence
    - image_path
    """

    # ---------------------------------------------------------
    # 초기화: OpenAI Client 설정
    # ---------------------------------------------------------
    def __init__(self):

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY env variable")

        # GPT-4o-mini 클라이언트
        self.llm = OpenAI(api_key=api_key)

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

        # GPT-4o-mini 호출
        res = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Extract biological entities and return ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )

        raw = res.choices[0].message.content.strip()

        # JSON decode
        try:
            data = json.loads(raw)
        except Exception:
            logger.error(f"[EntityNode] JSON Parse Error. Raw output: {raw}")
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
                logger.warning("[EntityNode] Invalid amino acids → resetting protein_sequence to null.")
                data["protein_sequence"] = None

        # Save to state
        state.entities = data
        state.log("entity_node", data)

        logger.info(f"[EntityNode] Extracted entities: {data}")
        return state

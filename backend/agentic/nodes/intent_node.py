# backend/agentic/nodes/intent_node.py

import logging
from typing import Dict, Any

from backend.agentic.state import HeliconState
from backend.agent.vision_reasoner import VisionReasoner

logger = logging.getLogger("IntentNode")
logging.basicConfig(level=logging.INFO)


class IntentNode:
    """
    사용자 질문을 기반으로 Intent를 분류하는 노드.
    멀티에이전트 파이프라인의 첫 번째 단계.
    """

    INTENT_LIST = [
        "protein_similarity",
        "disease_prediction",
        "therapeutic_recommendation",   # NEW
        "protein_design",
        "evidence_paths",
        "vision_reasoning",
        "general_search",
    ]

    def __init__(self):
        self.llm = VisionReasoner()   # 텍스트-only (이미지 없이도 작동)

    # ─────────────────────────────────────────────
    # 실행 함수
    # ─────────────────────────────────────────────
    def run(self, state: HeliconState) -> HeliconState:

        question = state.question

        prompt = f"""
You are an expert biomedical intent classifier.

Classify the user's question into EXACTLY ONE intent from the list:

{self.INTENT_LIST}

Descriptions:
- protein_similarity: find similar proteins or homologs
- disease_prediction: infer diseases associated with a protein
- therapeutic_recommendation: suggest therapeutic proteins / antibodies / peptides based on protein interactions
- protein_design: redesign or mutate protein sequences
- evidence_paths: retrieve graph-based biological evidence paths
- vision_reasoning: question involves figures, tables, diagrams, or visual inputs
- general_search: default for broad biological queries

Rules:
- Return ONLY one intent string from the list.
- No explanation.
- Answer in lowercase.

User question:
{question}
"""

        response = self.llm.reason(prompt)
        answer = response["answer"].strip().lower()

        # Normalize intent
        selected_intent = "general_search"
        for intent in self.INTENT_LIST:
            if intent in answer:
                selected_intent = intent
                break

        state.intent = selected_intent
        state.log("intent_node", {"intent": selected_intent})

        logger.info(f"[IntentNode] Intent classified: {selected_intent}")
        return state

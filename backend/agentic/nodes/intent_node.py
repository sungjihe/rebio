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
    멀티에이전트의 첫 번째 단계.
    """

    INTENT_LIST = [
        "protein_similarity",
        "disease_prediction",
        "drug_recommendation",
        "protein_design",
        "evidence_paths",
        "vision_reasoning",
        "general_search",
    ]

    def __init__(self):
        self.llm = VisionReasoner()   # 텍스트-only도 지원

    # ─────────────────────────────────────────────
    # 실행 함수
    # ─────────────────────────────────────────────
    def run(self, state: HeliconState) -> HeliconState:

        question = state.question

        prompt = f"""
You are an expert AI classifier for biomedical queries.

Classify the user's question into ONE intent from the following list:

{self.INTENT_LIST}

Descriptions:
- protein_similarity: find similar proteins
- disease_prediction: infer diseases associated with a protein
- drug_recommendation: suggest drugs based on protein targets
- protein_design: redesign or mutate protein sequences
- evidence_paths: retrieve graph-based biological evidence
- vision_reasoning: question involves tables, figures, images, or visual data
- general_search: default for general biology questions

Return ONLY one intent string.

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

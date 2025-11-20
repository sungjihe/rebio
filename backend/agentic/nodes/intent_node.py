# backend/agentic/nodes/intent_node.py

import logging
import os
import json
from typing import Dict, Any

from dotenv import load_dotenv
from openai import OpenAI
from backend.agentic.state import HeliconState

load_dotenv()

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
        "therapeutic_recommendation",
        "protein_design",
        "evidence_paths",
        "vision_reasoning",
        "general_search",
    ]

    # -----------------------------------------------------
    # 초기화: OpenAI LLM 클라이언트 설정
    # -----------------------------------------------------
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("Missing OPENAI_API_KEY env variable")

        self.llm = OpenAI(api_key=api_key)

    # -----------------------------------------------------
    # 실행 함수
    # -----------------------------------------------------
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

Return only one string.
"""

        # GPT-4o-mini 호출
        res = self.llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify biomedical query intent."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=50
        )

        answer = res.choices[0].message.content.strip().lower()

        # Intent normalization
        selected_intent = "general_search"
        for intent in self.INTENT_LIST:
            if intent in answer:
                selected_intent = intent
                break

        state.intent = selected_intent
        state.log("intent_node", {"intent": selected_intent})

        logger.info(f"[IntentNode] Intent classified: {selected_intent}")
        return state

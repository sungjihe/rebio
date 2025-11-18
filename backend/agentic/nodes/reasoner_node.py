# backend/agentic/nodes/reasoner_node.py
# backend/agentic/nodes/reasoner_node.py

import json
import logging
import torch
from openai import OpenAI

from transformers import AutoTokenizer, AutoModelForCausalLM
from backend.agentic.state import HeliconState

logger = logging.getLogger("ReasonerNode")
logging.basicConfig(level=logging.INFO)


class ReasonerNode:
    """
    ***Hybrid Reasoner Node***
    GPT-4o → BioMistral 2단 reasoning

    GPT-4o:
        - graph_result 통합
        - evidence_paths 정리
        - crawler/web data 요약
        - structure 정보 맥락화
        - 논문/리뷰 스타일 구조화

    BioMistral:
        - 단백질 기능/구조 reasoning
        - 약물 후보 논리적 평가
        - mutation 효과 분석
        - 질환/경로 기전 reasoning
        - 실험 제안 생성
    """

    def __init__(self, model_path="BioMistral/BioMistral-7B"):
        # GPT-4o client
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        # BioMistral
        logger.info(f"[ReasonerNode] Loading BioMistral ({model_path})…")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        self.device = device
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map="auto",
        )

    # ------------------------------------
    # GPT-4o summarizer
    # ------------------------------------
    def _gpt4o_integrate(self, prompt: str):
        response = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert biomedical summarizer."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=900,
            temperature=0.2
        )
        return response.choices[0].message.content

    # ------------------------------------
    # BioMistral
    # ------------------------------------
    def _biomistral(self, prompt: str):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=1000,
            temperature=0.35,
            top_p=0.9,
        )
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)

    # ------------------------------------
    # MAIN RUN
    # ------------------------------------
    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[ReasonerNode] Preparing multimodal reasoning context…")

        # 모든 정보를 prompt화
        prompt = f"""
Summarize and integrate the following biomedical evidence:

Entities:
{json.dumps(state.entities, indent=2)}

Graph Results (Neo4j):
{json.dumps(state.graph_result, indent=2)}

Evidence Paths:
{json.dumps(state.evidence_paths, indent=2)}

External Web Knowledge:
{json.dumps(state.enriched_data, indent=2)}

Protein Design Variants:
{json.dumps(state.designed_protein, indent=2)}

Structure Prediction:
PDB File: {state.structure_path}
Image: {state.structure_image}

Image-derived evidence:
{json.dumps(state.image_evidence, indent=2)}

Goal:
Produce a **high-level integrated scientific summary** suitable for a research report.
"""

        # ─────────────────────────────────────
        # 1) GPT-4o가 전체 정보 통합 → 고급 요약 생성
        # ─────────────────────────────────────
        gpt4o_summary = self._gpt4o_integrate(prompt)

        # ─────────────────────────────────────
        # 2) BioMistral이 domain reasoning 수행
        # ─────────────────────────────────────
        biom_prompt = f"""
Use the following integrated context to perform **deep biomedical reasoning**:

GPT-4o-integrated summary:
{gpt4o_summary}

Tasks:
- explain molecular mechanisms
- relate structure to function
- analyze mutations
- connect diseases
- evaluate drug candidates
- propose lab experiments
- summarize insights as a scientific report
"""

        final_output = self._biomistral(biom_prompt)

        state.reasoning = final_output
        state.log("reasoner_node", {"success": True})

        return state


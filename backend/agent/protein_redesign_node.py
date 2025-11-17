# backend/agent/protein_redesign_node.py
import os
import logging
from typing import List, Dict, Any, Optional

import torch
from pydantic import BaseModel, Field, validator

from dotenv import load_dotenv

# fair-esm
import esm

# OpenAI LLM (>=1.0 스타일)
from openai import OpenAI


# --------------------------------------------------------------------
# 환경 변수 로드
# --------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)

logger = logging.getLogger("ProteinRedesignNode")
logging.basicConfig(level=logging.INFO)


# --------------------------------------------------------------------
# 1) 입력 / 출력 스키마 (Pydantic)
# --------------------------------------------------------------------
class ProteinRedesignInput(BaseModel):
    sequence: str = Field(..., description="원본 단백질 아미노산 서열 (단일 폴리펩타이드)")
    num_variants: int = Field(
        3,
        ge=1,
        le=10,
        description="생성할 재설계 서열 개수 (1~10)",
    )
    max_mutation_rate: float = Field(
        0.05,
        ge=0.0,
        le=0.3,
        description="전체 길이 대비 최대 변이 비율 (예: 0.05 = 5%)",
    )
    design_goal: str = Field(
        "stability",
        description="재설계 목표 (예: 'stability', 'binding', 'expression')",
    )

    @validator("sequence")
    def validate_sequence(cls, v: str) -> str:
        seq = v.strip().upper()
        if not seq:
            raise ValueError("sequence는 비어 있으면 안 됩니다.")
        allowed = set("ACDEFGHIKLMNPQRSTVWY")
        invalid = {aa for aa in seq if aa not in allowed}
        if invalid:
            raise ValueError(
                f"유효하지 않은 아미노산 문자가 포함되어 있습니다: {invalid}"
            )
        return seq


class RedesignVariant(BaseModel):
    redesigned_sequence: str
    num_mutations: int
    mutation_positions: List[int]
    mutation_description: str
    esm2_score: float
    delta_score: float
    predicted_stability: str
    llm_rationale: str


class ProteinRedesignResult(BaseModel):
    original_sequence: str
    original_score: float
    variants: List[RedesignVariant]


# --------------------------------------------------------------------
# 2) ESM2 Scorer: esm2_t12_35M_UR50D
# --------------------------------------------------------------------
class ESM2Scorer:
    """
    ESM2 log-likelihood 기반 "안정성 proxy" 점수 계산기.
    - score_sequence: sequence 하나에 대한 평균 log_prob 점수 반환
    """

    def __init__(
        self,
        model_name: str = "esm2_t12_35M_UR50D",
        device: Optional[str] = None,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"[ESM2] Loading model {model_name} on {self.device} ...")
        self.model, self.alphabet = esm.pretrained.esm2_t12_35M_UR50D()
        self.model.eval()
        self.model.to(self.device)
        self.batch_converter = self.alphabet.get_batch_converter()

    @torch.no_grad()
    def score_sequence(self, seq: str) -> float:
        """
        ESM2 토큰 log_prob을 이용한 평균 log_likelihood 점수.
        값이 클수록 '모델이 보기엔 자연스러운'(진화적으로 plausible) 서열이라고 가정.
        """
        seq = seq.strip().upper()
        data = [("protein", seq)]
        batch_labels, batch_strs, batch_tokens = self.batch_converter(data)
        batch_tokens = batch_tokens.to(self.device)

        out = self.model(batch_tokens, repr_layers=[12], return_contacts=False)
        # token-level log_probs
        log_probs = self.model.forward_logits(batch_tokens)["logits"]
        log_probs = torch.log_softmax(log_probs, dim=-1)

        # 실제 토큰 인덱스
        tok_ids = batch_tokens[0, 1:-1]  # CLS/</s> 제거
        tok_log_probs = log_probs[0, 1:-1, :]
        ll = tok_log_probs[torch.arange(tok_ids.size(0)), tok_ids]

        return float(ll.mean().item())


# --------------------------------------------------------------------
# 3) LLM 기반 재설계 제안자
# --------------------------------------------------------------------
class LLMDesigner:
    """
    OpenAI GPT 기반 재설계 제안 모듈.
    - 입력: 원본 서열 + 목표
    - 출력: redesigned sequences + rationale
    """

    def __init__(self, model: str = "gpt-4o-mini"):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY가 .env에 설정되어 있지 않습니다.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def propose_variants(
        self,
        inp: ProteinRedesignInput,
    ) -> List[Dict[str, Any]]:
        """
        LLM에게 JSON 형태로 변이 제안을 받음.
        각 variant는 {sequence, rationale} 필드를 가짐.
        """
        system_prompt = (
            "You are an expert protein engineer. "
            "Given an amino acid sequence, you propose conservative mutations "
            "to improve the specified property (e.g., stability) while preserving "
            "overall fold and function. Return only JSON."
        )

        user_prompt = f"""
Original sequence (one-letter AA): {inp.sequence}

Design goal: {inp.design_goal}
Max mutation rate: {inp.max_mutation_rate:.2f}
Number of variants: {inp.num_variants}

Constraints:
- Preserve catalytic / binding motifs if any recognizable (e.g. HExxH, Cys2His2).
- Prefer conservative or semi-conservative substitutions.
- Avoid introducing too many Pro/Gly in helices or core.
- Avoid creating long runs of the same residue.

Return JSON with this schema:

{{
  "variants": [
    {{
      "redesigned_sequence": "...",
      "mutation_description": "e.g. A15V, L32I ...",
      "llm_rationale": "short explanation of why these mutations may help"
    }},
    ...
  ]
}}
        """

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            response_format={"type": "json_object"},
        )

        content = response.output[0].content[0].text
        import json

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"[LLMDesigner] JSON decode error: {e}")
            raise

        variants = data.get("variants", [])
        return variants


# --------------------------------------------------------------------
# 4) Protein Redesign Node (워크플로우 노드)
# --------------------------------------------------------------------
class ProteinRedesignNode:
    """
    단백질 재설계 워크플로우 노드

    입력:
        - ProteinRedesignInput (sequence, 목표, 변이 개수 등)

    내부:
        1) 입력 검증
        2) ESM2로 원본 서열 score
        3) LLM으로 후보 서열 제안
        4) 후보 서열 필터링 + ESM2 score
        5) Δscore 기준 정렬 + 안정성 라벨링

    출력:
        - ProteinRedesignResult
    """

    def __init__(self, esm_scorer: Optional[ESM2Scorer] = None,
                 llm_designer: Optional[LLMDesigner] = None):
        self.esm_scorer = esm_scorer or ESM2Scorer()
        self.llm_designer = llm_designer or LLMDesigner()

    def _predict_stability_label(self, delta_score: float) -> str:
        """
        Δscore (mut - wt)를 사용해 간단한 규칙 기반 stability 라벨링.
        """
        if delta_score > 0.3:
            return "likely more stable"
        if delta_score > 0.1:
            return "possibly more stable"
        if delta_score > -0.1:
            return "neutral / similar"
        if delta_score > -0.3:
            return "possibly less stable"
        return "likely destabilizing"

    def _compute_mutations(
        self,
        original: str,
        redesigned: str,
    ) -> Dict[str, Any]:
        """
        두 서열 비교해서 변이 위치, 개수, 문자열 설명 생성.
        """
        if len(original) != len(redesigned):
            return {
                "num_mutations": -1,
                "positions": [],
                "desc": "length_changed",
            }

        mutations = []
        positions = []
        for i, (wt, mt) in enumerate(zip(original, redesigned), start=1):
            if wt != mt:
                mutations.append(f"{wt}{i}{mt}")
                positions.append(i)

        desc = ", ".join(mutations) if mutations else "no_change"
        return {
            "num_mutations": len(mutations),
            "positions": positions,
            "desc": desc,
        }

    def run(self, inp: ProteinRedesignInput) -> ProteinRedesignResult:
        # 1) 입력 검증 (Pydantic이 1차로 검증함)
        seq = inp.sequence
        logger.info(
            f"[ProteinRedesignNode] Starting redesign for sequence "
            f"len={len(seq)}, goal={inp.design_goal}"
        )

        # 2) 원본 서열 ESM2 점수
        original_score = self.esm_scorer.score_sequence(seq)
        logger.info(f"[ProteinRedesignNode] Original ESM2 score: {original_score:.4f}")

        # 3) LLM을 통해 변이 서열 후보 생성
        raw_variants = self.llm_designer.propose_variants(inp)

        variants: List[RedesignVariant] = []
        for v in raw_variants:
            redesigned_seq = v.get("redesigned_sequence", "").strip().upper()
            rationale = v.get("llm_rationale", "")
            mutation_desc = v.get("mutation_description", "")

            # 기본적인 유효성 검사
            if not redesigned_seq:
                continue

            # 알파벳 검사 (입력과 동일 기준)
            allowed = set("ACDEFGHIKLMNPQRSTVWY")
            if any(aa not in allowed for aa in redesigned_seq):
                logger.warning(
                    "[ProteinRedesignNode] Skipping variant with invalid AA letters."
                )
                continue

            # 길이 검사 (지금은 길이 보존만 허용)
            if len(redesigned_seq) != len(seq):
                logger.warning(
                    "[ProteinRedesignNode] Skipping length-changing variant."
                )
                continue

            # 변이 개수 계산
            mut_info = self._compute_mutations(seq, redesigned_seq)
            num_mut = mut_info["num_mutations"]

            # max_mutation_rate 초과하면 skip
            max_allowed = int(len(seq) * inp.max_mutation_rate)
            if max_allowed == 0 and inp.max_mutation_rate > 0:
                max_allowed = 1
            if num_mut > max_allowed:
                logger.warning(
                    "[ProteinRedesignNode] Skipping variant with too many mutations "
                    f"({num_mut} > {max_allowed})"
                )
                continue

            # 4) ESM2 점수 계산
            variant_score = self.esm_scorer.score_sequence(designed_seq := redesigned_seq)
            delta = variant_score - original_score
            stability_label = self._predict_stability_label(delta)

            variants.append(
                RedesignVariant(
                    redesigned_sequence=redesigned_seq,
                    num_mutations=num_mut,
                    mutation_positions=mut_info["positions"],
                    mutation_description=mut_info["desc"] or mutation_desc,
                    esm2_score=variant_score,
                    delta_score=delta,
                    predicted_stability=stability_label,
                    llm_rationale=rationale,
                )
            )

        # 5) Δscore 기준 정렬 (안정성 향상 가능성이 높은 순)
        variants.sort(key=lambda x: x.delta_score, reverse=True)

        return ProteinRedesignResult(
            original_sequence=seq,
            original_score=original_score,
            variants=variants,
        )


if __name__ == "__main__":
    # 간단한 로컬 테스트 용도
    test_seq = "MEEPQSDPSVEPPLSQETFSDLWKLLPENNVLSPLPSQAMDDLMLSPDDI"
    inp = ProteinRedesignInput(
        sequence=test_seq,
        num_variants=3,
        max_mutation_rate=0.05,
        design_goal="stability",
    )
    node = ProteinRedesignNode()
    result = node.run(inp)
    print(result.model_json(indent=2))

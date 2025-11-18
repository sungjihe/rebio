# backend/agentic/nodes/designer_node.py

import logging
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from pydantic import BaseModel
from typing import List, Dict, Any
import esm
import os

from backend.agentic.state import HeliconState

logger = logging.getLogger("DesignNode")
logging.basicConfig(level=logging.INFO)


# ============================
# ESM2 Scorer
# ============================

class ESM2Scorer:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.model, self.alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        self.model.to(device).eval()
        self.converter = self.alphabet.get_batch_converter()

    @torch.no_grad()
    def score(self, seq: str) -> float:
        data = [("protein", seq)]
        _, _, tokens = self.converter(data)
        tokens = tokens.to(self.device)

        logits = self.model(tokens)["logits"]
        log_probs = torch.log_softmax(logits, dim=-1)

        tok_ids = tokens[0, 1:-1]
        tok_log_probs = log_probs[0, 1:-1]

        ll = tok_log_probs[torch.arange(len(tok_ids)), tok_ids]
        return float(ll.mean().item())


# ============================
# DesignerNode (BioMistral)
# ============================

class DesignNode:
    """
    오픈소스 BioMistral 모델 기반 단백질 재설계 에이전트
    """

    def __init__(
        self,
        model_path: str = "BioMistral/BioMistral-7B",
        num_variants: int = 3
    ):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        logger.info(f"[DesignNode] Loading BioMistral… {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto"
        )

        self.num_variants = num_variants
        self.scorer = ESM2Scorer()

    def generate_variants(self, seq: str) -> List[Dict[str, str]]:
        prompt = f"""
You are a protein engineering expert.
Propose {self.num_variants} redesigned variants for the protein sequence below.

Sequence:
{seq}

Return ONLY JSON:
{{
  "variants": [
    {{
      "sequence": "...",
      "mutation_description": "...",
      "rationale": "..."
    }}
  ]
}}
"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        output = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.5,
            top_p=0.9,
        )

        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)

        import json
        try:
            data = json.loads(decoded.split("{",1)[1])  # JSON 부분만 추출
        except:
            logger.error("[DesignNode] Failed to decode JSON output.")
            return []

        return data["variants"]

    def run(self, state: HeliconState) -> HeliconState:
        seq = state.entities.get("protein_sequence")
        if not seq:
            logger.info("[DesignNode] No protein_sequence. Skipping.")
            return state

        logger.info("[DesignNode] Designing variants...")

        wt_score = self.scorer.score(seq)
        raw_variants = self.generate_variants(seq)

        processed = []
        for v in raw_variants:
            new_seq = v["sequence"]
            new_score = self.scorer.score(new_seq)
            delta = new_score - wt_score

            processed.append({
                "sequence": new_seq,
                "esm2_score": new_score,
                "delta_score": delta,
                "mutation_description": v["mutation_description"],
                "rationale": v["rationale"]
            })

        state.designed_protein = processed
        state.log("design_node", {"variants": len(processed)})

        return state

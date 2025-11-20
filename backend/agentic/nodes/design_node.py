# backend/agentic/nodes/design_node.py

import logging
import torch
import json
from typing import List, Dict, Any
from transformers import AutoTokenizer, AutoModelForCausalLM
import esm

from backend.agentic.state import HeliconState

logger = logging.getLogger("DesignNode")
logging.basicConfig(level=logging.INFO)


# ============================================================
# ESM2 SCORER (Protein sequence scoring)
# ============================================================
class ESM2Scorer:
    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device

        logger.info(f"[ESM2Scorer] Loading ESM2 (650M)… on {device}")
        self.model, self.alphabet = esm.pretrained.esm2_t33_650M_UR50D()
        self.model = self.model.to(device).eval()
        self.converter = self.alphabet.get_batch_converter()

    @torch.no_grad()
    def score(self, seq: str) -> float:
        """Return per-token mean log-likelihood score."""
        data = [("protein", seq)]
        _, _, tokens = self.converter(data)
        tokens = tokens.to(self.device)

        outputs = self.model(tokens)
        logits = outputs["logits"]
        log_probs = torch.log_softmax(logits, dim=-1)

        ids = tokens[0, 1:-1]
        per_tok = log_probs[0, 1:-1]

        ll = per_tok[torch.arange(len(ids)), ids]
        return float(ll.mean().item())


# ============================================================
# DESIGN NODE
# ============================================================
class DesignNode:
    """
    BioMistral 기반 Protein Design Node
    - 변이 제안
    - ESM2로 score 계산
    """

    def __init__(self, model_path="BioMistral/BioMistral-7B", num_variants=3):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = device
        self.num_variants = num_variants

        logger.info(f"[DesignNode] Loading BioMistral model: {model_path}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            device_map="auto",
        )

        self.scorer = ESM2Scorer()

    # ---------------------------------------------------
    def _generate(self, seq: str) -> List[Dict[str, Any]]:
        """BioMistral로 변이 후보 생성"""

        prompt = f"""
You are a protein engineering expert.
Propose {self.num_variants} redesigned variants for the protein sequence below.

Sequence:
{seq}

Return ONLY this JSON structure:

{{
  "variants": [
    {{
      "sequence": "STRING",
      "mutation_description": "STRING",
      "rationale": "STRING"
    }}
  ]
}}
"""

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)
        output = self.model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=True,
            temperature=0.6,
            top_p=0.9
        )

        decoded = self.tokenizer.decode(output[0], skip_special_tokens=True)

        # JSON robust extraction
        start = decoded.find("{")
        end = decoded.rfind("}") + 1
        if start == -1 or end == -1:
            logger.error("[DesignNode] JSON not found in output.")
            return []

        json_part = decoded[start:end]

        try:
            data = json.loads(json_part)
            return data.get("variants", [])
        except Exception as e:
            logger.error(f"[DesignNode] Failed to parse JSON: {e}")
            return []

    # ---------------------------------------------------
    def run(self, state: HeliconState) -> HeliconState:

        seq = state.entities.get("protein_sequence")
        if not seq:
            logger.info("[DesignNode] No input sequence found. Skipping.")
            return state

        logger.info("[DesignNode] Generating redesigned variants…")

        # WT score
        wt_score = self.scorer.score(seq)

        # Generate candidates
        variants = self._generate(seq)

        processed = []
        for v in variants:
            new_seq = v.get("sequence")
            if not new_seq:
                continue

            score = self.scorer.score(new_seq)
            processed.append({
                "sequence": new_seq,
                "esm2_score": score,
                "delta_score": score - wt_score,
                "mutation_description": v.get("mutation_description"),
                "rationale": v.get("rationale"),
            })

        state.designed_protein = processed
        state.log("design_node", {"variants": len(processed)})

        return state

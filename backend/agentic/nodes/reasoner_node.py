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
    ReasonerNode v2:
    - GPT-4o summary
    - BioMistral deep reasoning
    - explicitly uses z-score, weight, hop-penalty info
    """

    def __init__(self, model_path="BioMistral/BioMistral-7B"):
        self.openai = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        device = "cuda" if torch.cuda.is_available() else "cpu"
        dtype = torch.float16 if device == "cuda" else torch.float32

        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=dtype,
            device_map="auto",
        )

    def _gpt4o_integrate(self, prompt):
        res = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert biomedical summarizer."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.25,
            max_tokens=900
        )
        return res.choices[0].message.content

    def _biomistral(self, prompt):
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=1200,
            temperature=0.35,
            top_p=0.9,
        )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    def run(self, state: HeliconState) -> HeliconState:
        # Build integrated prompt
        prompt = f"""
Integrate the following biomedical evidence.

Entities:
{json.dumps(state.entities, indent=2)}

Graph Results:
{json.dumps(state.graph_result, indent=2)}

Evidence Path Scores (Normalized):
Explain the influence of:
- z-score
- evidence type weights
- hop penalties
- path structural strength

{json.dumps(state.evidence_paths, indent=2)}

External Knowledge:
{json.dumps(state.enriched_data, indent=2)}

Goal:
Produce a logically consistent, mechanistic explanation that reflects:
- strong (direct) evidence as primary
- similarity-based signals as secondary
- hop-penalized evidence as weaker
        """

        gpt_summary = self._gpt4o_integrate(prompt)

        deep_prompt = f"""
Use the following high-level summary plus normalized evidence scores:

{gpt_summary}

Tasks:
- integrate structure-function relationships
- evaluate mechanistic plausibility
- propose drug repurposing hypotheses
- emphasize statistically strong (high z-score) evidence
        """

        biom = self._biomistral(deep_prompt)

        state.reasoning_summary = gpt_summary
        state.reasoning = biom
        return state

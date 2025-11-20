# backend/agentic/nodes/reasoner_node.py

import os
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
    ReasonerNode v3 — TherapeuticProtein version
    --------------------------------------------
    - GPT-4o summarization
    - BioMistral mechanistic reasoning
    - Understands:
        * Protein → Disease
        * TherapeuticProtein → Protein (TARGETS/BINDS/MODULATES)
        * Protein similarity propagation
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
        logger.info(f"[ReasonerNode] Loaded BioMistral on {device}")

    # -----------------------------------------------------
    # GPT-4o integration
    # -----------------------------------------------------
    def _gpt4o_integrate(self, prompt: str) -> str:
        res = self.openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are an expert biomedical summarizer specialized in protein therapeutics."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=900
        )
        return res.choices[0].message.content

    # -----------------------------------------------------
    # BioMistral deep reasoning
    # -----------------------------------------------------
    def _biomistral(self, prompt: str) -> str:
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        out = self.model.generate(
            **inputs,
            max_new_tokens=1400,
            temperature=0.35,
            top_p=0.9,
        )
        return self.tokenizer.decode(out[0], skip_special_tokens=True)

    # -----------------------------------------------------
    # RUN
    # -----------------------------------------------------
    def run(self, state: HeliconState) -> HeliconState:

        # Build evidence-integrated prompt
        prompt = f"""
You are an expert in therapeutic protein biology.

Summarize and integrate the following evidence:

Entities:
{json.dumps(state.entities, indent=2)}

Graph Results (Disease / TherapeuticProtein):
{json.dumps(state.graph_result, indent=2)}

Evidence Path Scores:
- include z-score meaning
- hop penalties
- relationship weights (TARGETS, BINDS_TO, MODULATES)
- protein similarity propagation
{json.dumps(state.evidence_paths, indent=2)}

External Knowledge:
{json.dumps(state.enriched_data, indent=2)}

Goal:
Produce a mechanistic, protein-centric explanation.
Prioritize:
1. direct evidence (TARGETS/BINDS/MODULATES)
2. protein-disease edges
3. similarity-based indirect evidence
4. path-penalized weak evidence

Keep the reasoning scientific and structured.
"""

        # GPT-4o summary stage
        gpt_summary = self._gpt4o_integrate(prompt)

        # Deep mechanistic reasoning
        deep_prompt = f"""
Here is the high-level summary:

{gpt_summary}

Using the above, produce:
- mechanistic explanation (protein function → disease)
- how therapeutic proteins might modulate these pathways
- evaluate statistical strength (z-score, weights)
- propose therapeutic hypotheses

Keep it scientific and concise.
"""

        biom = self._biomistral(deep_prompt)

        state.reasoning_summary = gpt_summary
        state.reasoning = biom
        logger.info("[ReasonerNode] Completed reasoning integration")

        return state

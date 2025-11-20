# backend/agentic/nodes/final_node.py

import json
import logging
from typing import Any

from backend.agentic.state import HeliconState

logger = logging.getLogger("FinalNode")
logging.basicConfig(level=logging.INFO)


class FinalNode:
    """
    최종 사용자 응답을 조립하는 노드.
    모든 노드의 결과를 Markdown + JSON 형태로 안전하게 병합한다.
    """

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[FinalNode] Building final response...")

        # -------------------------------
        # 1) Core components
        # -------------------------------
        entities = state.entities or {}
        intent = state.intent

        graph = state.graph_result
        evidence = state.evidence_paths
        enrich = state.enriched_data
        design = state.designed_protein
        structure = state.structure_result
        vision = state.vision_data

        reasoning_summary = getattr(state, "reasoning_summary", None)
        reasoning = state.reasoning

        # -------------------------------
        # 2) Markdown Summary (safe)
        # -------------------------------
        summary_md = (
f"# 🧬 Helicon AI – Bio-Agentic Analysis Report\n"
f"## 🔍 Intent\n"
f"**{intent}**\n"
f"---\n\n"

f"## 🧩 Extracted Entities\n"
f"```json\n"
f"{json.dumps(entities, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 🧠 GPT-4o Integrated Summary\n"
f"```markdown\n"
f"{reasoning_summary}\n"
f"```\n\n"

f"## 🔬 BioMistral Scientific Reasoning\n"
f"```markdown\n"
f"{reasoning}\n"
f"```\n\n"

f"## 🧬 Protein Design Variants\n"
f"```json\n"
f"{json.dumps(design, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 🧱 Structure Prediction (ESMFold)\n"
f"```json\n"
f"{json.dumps(structure, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 👁 Vision-based Evidence (BLIP2 + GPT-4o + BioMistral)\n"
f"```json\n"
f"{json.dumps(vision, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 🔗 Graph Search Result (Neo4j)\n"
f"```json\n"
f"{json.dumps(graph, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 🧭 Evidence Paths (Graph Reasoning)\n"
f"```json\n"
f"{json.dumps(evidence, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"## 🌐 External Knowledge (Crawler)\n"
f"```json\n"
f"{json.dumps(enrich, indent=2, ensure_ascii=False)}\n"
f"```\n\n"

f"---\n"
f"## 📝 Final Notes\n"
f"- GraphDB evidence\n"
f"- Web knowledge\n"
f"- Protein design\n"
f"- Structure prediction\n"
f"- Vision-based extraction\n"
f"- GPT-4o + BioMistral reasoning\n"
        )

        # -------------------------------
        # 3) JSON Output (frontend)
        # -------------------------------
        final_json = {
            "intent": intent,
            "entities": entities,
            "graph_result": graph,
            "evidence_paths": evidence,
            "enriched_data": enrich,
            "designed_protein": design,
            "structure_result": structure,
            "vision_data": vision,
            "reasoning_summary": reasoning_summary,
            "reasoning_scientific": reasoning,
            "markdown_summary": summary_md,
        }

        state.final_output = final_json
        state.log("final_node", {"success": True})
        return state

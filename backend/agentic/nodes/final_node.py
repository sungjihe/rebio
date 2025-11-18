# backend/agentic/nodes/final_node.py

import json
import logging
from typing import Dict, Any

from backend.agentic.state import HeliconState

logger = logging.getLogger("FinalNode")
logging.basicConfig(level=logging.INFO)


class FinalNode:
    """
    최종 사용자 응답을 조립하는 노드.
    모든 노드의 결과를 합쳐 사용자에게 보여줄 수 있는 최종 formatted output 생성.

    출력 형태:
        state.final_output = {
            "summary_markdown": "...",
            "reasoning": "...",
            "structure_image": "path/to/png",
            "pdb_file": "path/to.pdb",
            "designed_variants": [...],
            "graph_result": [...],
            "evidence_paths": [...],
            "enriched_data": {...}
        }
    """

    def __init__(self):
        pass

    def run(self, state: HeliconState) -> HeliconState:
        logger.info("[FinalNode] Building final user-facing response…")

        reasoning = state.reasoning
        graph_res = state.graph_result
        evidence = state.evidence_paths
        enriched = state.enriched_data
        structure_img = state.structure_image
        pdb_file = state.structure_path
        design = state.designed_protein

        # ---------------------------------------------------
        # Markdown Summary (User-friendly)
        # ---------------------------------------------------
        summary_md = f"""
# 🧬 Helicon AI – Bio-Agentic Analysis Report

## 1. Intent
**{state.intent}**

## 2. Entities
```json
{json.dumps(state.entities, indent=2, ensure_ascii=False)}

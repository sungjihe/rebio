# backend/agentic/nodes/evidence_node.py

import logging
from typing import Any, Dict, Optional

from backend.agentic.state import HeliconState
from backend.graph.graph_search_client import GraphSearchClient

logger = logging.getLogger("EvidenceNode")
logging.basicConfig(level=logging.INFO)


class EvidenceNode:
    """
    Neo4j에서 '근거 그래프 경로(Evidence Path)'를 추출하는 에이전트 노드.

    사용 시나리오:
      - disease_prediction → Protein-Disease evidence path
      - drug_recommendation → Protein-Drug evidence path
      - evidence_paths → 사용자가 직접 요청한 경우
    """

    def __init__(self, max_paths: int = 5, max_hops: int = 4):
        self.max_paths = max_paths
        self.max_hops = max_hops

    # ─────────────────────────────────────────────
    # 실행 함수
    # ─────────────────────────────────────────────
    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        entities = state.entities or {}
        graph_result = state.graph_result

        uniprot_id = entities.get("uniprot_id")
        if not uniprot_id:
            logger.warning("[EvidenceNode] No uniprot_id found. Skipping.")
            state.evidence_paths = None
            return state

        # ============================================
        # 1) 어떤 타겟(disease or drug)을 evidence로 찾을지 결정
        # ============================================
        target_id = None
        mode = None  # protein_disease or protein_drug

        if intent == "disease_prediction" and graph_result:
            target_id = graph_result[0].get("disease_id")
            mode = "protein_disease"

        elif intent == "drug_recommendation" and graph_result:
            target_id = graph_result[0].get("drugbank_id")
            mode = "protein_drug"

        elif intent == "evidence_paths":
            # User explicitly asked for evidence
            if entities.get("disease_id"):
                target_id = entities["disease_id"]
                mode = "protein_disease"
            elif entities.get("drugbank_id"):
                target_id = entities["drugbank_id"]
                mode = "protein_drug"

        # ============================================
        # evidence path를 찾을 이유가 없으면 skip
        # ============================================
        if not target_id or not mode:
            logger.info("[EvidenceNode] No target for evidence path. Skipping.")
            state.evidence_paths = None
            state.log("evidence_node", {"skipped": True})
            return state

        logger.info(f"[EvidenceNode] Finding evidence path: {uniprot_id} → {target_id} ({mode})")

        client = GraphSearchClient()
        paths = None

        try:
            if mode == "protein_disease":
                paths = client.evidence_paths_protein_disease(
                    uniprot_id,
                    target_id,
                    max_paths=self.max_paths,
                    max_hops=self.max_hops,
                )

            elif mode == "protein_drug":
                paths = client.evidence_paths_protein_drug(
                    uniprot_id,
                    target_id,
                    max_paths=self.max_paths,
                    max_hops=self.max_hops,
                )

        except Exception as e:
            logger.error(f"[EvidenceNode] Failed to fetch evidence paths: {e}")
            paths = None

        finally:
            client.close()

        # 저장
        state.evidence_paths = paths
        state.log("evidence_node", {
            "mode": mode,
            "target_id": target_id,
            "path_count": len(paths or []),
        })

        return state

# backend/agentic/nodes/graph_node.py

import logging
from typing import List, Dict, Any, Optional

from backend.agentic.state import HeliconState
from backend.graph.graph_search_client import GraphSearchClient

logger = logging.getLogger("GraphNode")
logging.basicConfig(level=logging.INFO)


class GraphNode:
    """
    Neo4j 기반 단백질-질병-약물 그래프 탐색 에이전트.
    intent + uniprot_id를 기반으로 적절한 그래프 쿼리를 수행한다.
    """

    def __init__(self, top_k: int = 20):
        self.top_k = top_k

    # ─────────────────────────────────────────────
    # 실행 함수
    # ─────────────────────────────────────────────
    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        entities = state.entities or {}
        uniprot_id = entities.get("uniprot_id")

        if not uniprot_id:
            logger.warning("[GraphNode] No uniprot_id found in entities. Skipping graph query.")
            state.graph_result = None
            state.log("graph_node", {"error": "no_uniprot_id"})
            return state

        if intent not in ("protein_similarity", "disease_prediction", "drug_recommendation"):
            logger.info(f"[GraphNode] Intent '{intent}' does not require graph query. Skipping.")
            state.graph_result = None
            state.log("graph_node", {"skipped_for_intent": intent})
            return state

        logger.info(f"[GraphNode] Running graph query for intent={intent}, uniprot_id={uniprot_id}")

        client = GraphSearchClient()
        result: Optional[List[Dict[str, Any]]] = None

        try:
            if intent == "protein_similarity":
                result = client.similar_proteins(uniprot_id, top_k=self.top_k)

            elif intent == "disease_prediction":
                result = client.predict_diseases(uniprot_id, top_k=self.top_k)

            elif intent == "drug_recommendation":
                result = client.recommend_drugs(uniprot_id, top_k=self.top_k)

            logger.info(f"[GraphNode] Retrieved {len(result or [])} records from Neo4j.")

        except Exception as e:
            logger.error(f"[GraphNode] Graph query failed: {e}")
            result = None

        finally:
            client.close()

      
        state.graph_result = result
        state.log("graph_node", {"intent": intent, "uniprot_id": uniprot_id, "result_count": len(result or [])})

        return state

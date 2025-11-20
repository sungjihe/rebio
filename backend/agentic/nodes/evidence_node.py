# backend/agentic/nodes/evidence_node.py

import logging
from backend.agentic.state import HeliconState
from backend.graph.graph_search_client import GraphSearchClient

logger = logging.getLogger("EvidenceNode")
logging.basicConfig(level=logging.INFO)


class EvidenceNode:
    """
    EvidenceNode v3 — TherapeuticProtein version
    - disease_prediction → disease evidence
    - therapeutic_recommendation → therapeutic protein evidence
    """

    def __init__(self, max_paths=5, max_hops=4):
        self.max_paths = max_paths
        self.max_hops = max_hops

    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        entities = state.entities or {}
        graph = state.graph_result or []

        uniprot_id = entities.get("uniprot_id")
        if not uniprot_id:
            state.evidence_paths = None
            return state

        # ------------------------------------------
        # 1) Target selection (depends on intent)
        # ------------------------------------------
        target_id = None

        # Disease prediction → use disease_id
        if intent == "disease_prediction" and graph:
            target_id = graph[0].get("disease_id")

        # Therapeutic recommendation → use therapeutic protein uniprot_id
        elif intent == "therapeutic_recommendation" and graph:
            target_id = graph[0].get("uniprot_id")

        # Nothing to do
        if not target_id:
            state.evidence_paths = None
            return state

        # ------------------------------------------
        # 2) Query evidence paths
        # ------------------------------------------
        client = GraphSearchClient()

        try:
            paths = client.evidence_paths(
                uniprot_id,
                target_id,
                max_paths=self.max_paths,
                max_hops=self.max_hops
            )
        except Exception as e:
            logger.error(f"[EvidenceNode] Evidence path error: {e}")
            paths = None
        finally:
            client.close()

        # ------------------------------------------
        # 3) Save result
        # ------------------------------------------
        state.evidence_paths = paths
        return state

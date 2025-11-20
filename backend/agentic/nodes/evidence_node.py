# backend/agentic/nodes/evidence_node.py

import logging
from backend.agentic.state import HeliconState
from backend.graph.graph_search_client import GraphSearchClient

logger = logging.getLogger("EvidenceNode")
logging.basicConfig(level=logging.INFO)


class EvidenceNode:
    """
    EvidenceNode v2
    - GraphSearchClient.evidence_paths()의 full v2 scoring을 그대로 state에 저장
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

        target_id = None
        if intent == "disease_prediction" and graph:
            target_id = graph[0]["disease_id"]
        elif intent == "drug_recommendation" and graph:
            target_id = graph[0]["drugbank_id"]

        if not target_id:
            state.evidence_paths = None
            return state

        client = GraphSearchClient()
        try:
            paths = client.evidence_paths(
                uniprot_id,
                target_id,
                max_paths=self.max_paths,
                max_hops=self.max_hops
            )
        except Exception as e:
            logger.error(f"Evidence path error: {e}")
            paths = None
        finally:
            client.close()

        state.evidence_paths = paths
        return state

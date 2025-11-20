# backend/agentic/nodes/graph_node.py

import logging
from typing import List, Dict, Any, Optional

from backend.agentic.state import HeliconState
from backend.graph.graph_search_client import GraphSearchClient

logger = logging.getLogger("GraphNode")
logging.basicConfig(level=logging.INFO)


class GraphNode:
    """
    GraphNode (TherapeuticProtein version)
    - protein_similarity
    - disease_prediction
    - therapeutic_recommendation
    """

    def __init__(self, top_k: int = 20):
        self.top_k = top_k

    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        entities = state.entities or {}
        uniprot_id = entities.get("uniprot_id")

        if not uniprot_id:
            logger.warning("[GraphNode] No uniprot_id found.")
            state.graph_result = None
            return state

        # Supported intents
        if intent not in (
            "protein_similarity",
            "disease_prediction",
            "therapeutic_recommendation",
        ):
            logger.info(f"[GraphNode] Intent '{intent}' does not require graph.")
            state.graph_result = None
            return state

        client = GraphSearchClient()
        result = None

        try:
            if intent == "protein_similarity":
                result = client.similar_proteins(uniprot_id, self.top_k)

            elif intent == "disease_prediction":
                result = client.predict_diseases(uniprot_id, self.top_k)

            elif intent == "therapeutic_recommendation":
                # 🔥 NEW: therapeutic recommendation
                result = client.recommend_therapeutics(uniprot_id, self.top_k)

        finally:
            client.close()

        state.graph_result = result
        logger.info(f"[GraphNode] Graph result retrieved ({intent})")
        return state


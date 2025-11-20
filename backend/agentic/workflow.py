# backend/agentic/workflow.py

import logging
from langgraph.graph import StateGraph, END
from backend.agentic.state import HeliconState

# Nodes
from backend.agentic.nodes.supervisor_node import SupervisorNode
from backend.agentic.nodes.intent_node import IntentNode
from backend.agentic.nodes.entity_node import EntityNode
from backend.agentic.nodes.vision_node import VisionNode
from backend.agentic.nodes.graph_node import GraphNode
from backend.agentic.nodes.evidence_node import EvidenceNode
from backend.agentic.nodes.crawler_node import CrawlerNode
from backend.agentic.nodes.design_node import DesignNode
from backend.agentic.nodes.structure_node import StructureNode
from backend.agentic.nodes.render_node import RenderNode
from backend.agentic.nodes.reasoner_node import ReasonerNode
from backend.agentic.nodes.final_node import FinalNode

logger = logging.getLogger("HeliconWorkflow")
logging.basicConfig(level=logging.INFO)

def supervisor_decider(state: HeliconState):
    return state.next_node

def build_workflow():
    graph = StateGraph(HeliconState)

    # Register nodes
    graph.add_node("supervisor", SupervisorNode().run)
    graph.add_node("intent", IntentNode().run)
    graph.add_node("entity", EntityNode().run)
    graph.add_node("vision", VisionNode().run)
    graph.add_node("graph", GraphNode().run)
    graph.add_node("evidence", EvidenceNode().run)
    graph.add_node("crawler", CrawlerNode().run)
    graph.add_node("design", DesignNode().run)
    graph.add_node("structure", StructureNode().run)
    graph.add_node("render", RenderNode().run)
    graph.add_node("reason", ReasonerNode().run)
    graph.add_node("final", FinalNode().run)

    # Entry
    graph.set_entry_point("supervisor")

    # Routing
    graph.add_conditional_edges(
        source="supervisor",
        condition=supervisor_decider,
        edge_map={
            "intent": "intent",
            "entity": "entity",
            "vision": "vision",
            "graph": "graph",
            "evidence": "evidence",
            "crawler": "crawler",
            "design": "design",
            "structure": "structure",
            "render": "render",
            "reason": "reason",
            "final": "final",
        }
    )

    # All nodes except final go back to supervisor
    for n in [
        "intent", "entity", "vision", "graph",
        "evidence", "crawler", "design",
        "structure", "render", "reason"
    ]:
        graph.add_edge(n, "supervisor")

    graph.add_edge("final", END)

    return graph

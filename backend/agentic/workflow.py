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


# -----------------------------------------------------
# Supervisor routing rule
# -----------------------------------------------------
def supervisor_decider(state: HeliconState):
    """
    Read SupervisorNode.next_node and route accordingly.
    """
    return state.next_node


# -----------------------------------------------------
# Build LangGraph multi-agent workflow
# -----------------------------------------------------
def build_workflow():
    graph = StateGraph(HeliconState)

    # 1) Register nodes
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

    # 2) Entry point
    graph.set_entry_point("supervisor")

    # 3) Dynamic routing: supervisor → next_node
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

    # 4) After each node → return to supervisor
    for node in [
        "intent", "entity", "vision", "graph",
        "evidence", "crawler", "design",
        "structure", "render", "reason"
    ]:
        graph.add_edge(node, "supervisor")

    # 5) Final → END
    graph.add_edge("final", END)

    return graph

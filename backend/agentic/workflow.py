# backend/agentic/workflow.py

import logging
from langgraph.graph import StateGraph, END

# Helicon State
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


# ============================================================
#  Multi-Agent StateGraph Assembly
# ============================================================
def build_workflow():
    graph = StateGraph(HeliconState)

    # 1) Register nodes
    graph.add_node("supervisor", SupervisorNode().run)
    graph.add_node("intent", IntentNode().run)
    graph.add_node("entity", EntityNode().run)
    graph.add_node("vision", VisionNode().run)  # ← NEW: 업그레이드된 VisionNode 포함
    graph.add_node("graph", GraphNode().run)
    graph.add_node("evidence", EvidenceNode().run)
    graph.add_node("crawler", CrawlerNode().run)
    graph.add_node("design", DesignNode().run)
    graph.add_node("structure", StructureNode().run)
    graph.add_node("render", RenderNode().run)
    graph.add_node("reason", ReasonerNode().run)  # ← NEW: 하이브리드 ReasonerNode 포함
    graph.add_node("final", FinalNode().run)

    # 2) Set entry point
    graph.set_entry_point("supervisor")

    # 3) Static edges (Supervisor chooses next via dynamic routing)
    graph.add_edge("supervisor", "intent")
    graph.add_edge("intent", "entity")
    graph.add_edge("entity", "vision")   # ← 이미지가 있을 때 VisionNode가 먼저 실행됨
    graph.add_edge("vision", "graph")    # Vision → graph search

    graph.add_edge("graph", "evidence")
    graph.add_edge("evidence", "crawler")
    graph.add_edge("crawler", "design")
    graph.add_edge("design", "structure")
    graph.add_edge("structure", "render")
    graph.add_edge("render", "reason")
    graph.add_edge("reason", "final")

    graph.add_edge("final", END)

    return graph

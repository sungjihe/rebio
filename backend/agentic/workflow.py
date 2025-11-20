# backend/agentic/workflow.py

import logging
from typing import Any

from langgraph.graph import StateGraph, END
from backend.agentic.state import HeliconState

# Nodes
from backend.agentic.nodes.supervisor_node import SupervisorNode
from backend.agentic.nodes.intent_node import IntentNode
from backend.agentic.nodes.entity_node import EntityNode
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


# ─────────────────────────────────────────────
# 1) Supervisor가 다음 노드를 결정하는 함수
# ─────────────────────────────────────────────
def supervisor_decider(state: HeliconState) -> str:
    """
    SupervisorNode 가 state.next_node 에 기록해 둔 값 기반으로
    LangGraph의 conditional edge가 라우팅되도록 하는 함수.
    """
    # SupervisorNode.run 이 반드시 다음 노드 이름을 여기에 넣어줘야 함.
    next_node = getattr(state, "next_node", None)
    if not next_node:
        # 안전장치: 지정 안 되면 곧바로 final 로 보냄
        return "final"
    return next_node


# ─────────────────────────────────────────────
# 2) 그래프 빌더
# ─────────────────────────────────────────────
def build_workflow():
    """
    langgraph 1.x StateGraph API 기반 Helicon 멀티에이전트 워크플로우.
    """
    # state_schema 로 HeliconState 사용
    graph = StateGraph(HeliconState)

    # ── 노드 등록 (add_node) ──────────────────
    graph.add_node("supervisor", SupervisorNode().run)
    graph.add_node("intent", IntentNode().run)
    graph.add_node("entity", EntityNode().run)
    graph.add_node("graph", GraphNode().run)
    graph.add_node("crawler", CrawlerNode().run)
    graph.add_node("evidence", EvidenceNode().run)
    graph.add_node("design", DesignNode().run)
    graph.add_node("structure", StructureNode().run)
    graph.add_node("render", RenderNode().run)
    graph.add_node("reasoner", ReasonerNode().run)
    graph.add_node("final", FinalNode().run)

    # ── Entry point: supervisor ───────────────
    graph.set_entry_point("supervisor")

    # ── Supervisor 에서 다음 노드로 조건 분기 ──
    # state.next_node 값이 key 로 들어오면, 해당 value 노드로 이동
    graph.add_conditional_edges(
        "supervisor",
        supervisor_decider,
        {
            "intent": "intent",
            "entity": "entity",
            "graph": "graph",
            "crawler": "crawler",
            "evidence": "evidence",
            "design": "design",
            "structure": "structure",
            "render": "render",
            "reasoner": "reasoner",
            "final": "final",
            # 혹시 Supervisor가 "END" 를 직접 넣으면 그래프 종료
            "END": END,
        },
    )

    # ── 각 작업 노드 실행 후 다시 supervisor 로 복귀 ──
    for node_name in [
        "intent",
        "entity",
        "graph",
        "crawler",
        "evidence",
        "design",
        "structure",
        "render",
        "reasoner",
    ]:
        graph.add_edge(node_name, "supervisor")

    # ── final 에 도달하면 종료 ────────────────
    graph.set_finish_point("final")

    # ── 컴파일 ────────────────────────────────
    compiled = graph.compile()
    return compiled


# 전역에서 한 번 빌드해서 재사용
workflow = build_workflow()


# ─────────────────────────────────────────────
# 3) FastAPI 에서 사용할 진입 함수
# ─────────────────────────────────────────────
def run_helicon(initial_state: HeliconState | dict[str, Any]):
    """
    FastAPI 라우터에서 사용하는 얇은 래퍼.

    - initial_state 를 HeliconState (혹은 dict 호환) 형태로 받아서
      LangGraph workflow.invoke() 에 그대로 넘긴다.
    - HeliconState 를 TypedDict 로 정의했다면 dict 도 그대로 사용 가능.
    """
    # dict 로 들어온 경우, 그대로 넘겨도 되고,
    # HeliconState 가 dataclass / Pydantic Model 이라면 여기서 캐스팅해도 됨.
    logger.info("[HeliconWorkflow] run_helicon invoked")
    result = workflow.invoke(initial_state)
    return result

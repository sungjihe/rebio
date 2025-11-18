# backend/agentic/state.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HeliconState(BaseModel):
    """
    Multi-Agent 전체 상태를 관리하는 중앙 state 모델.
    모든 노드는 이 State를 입력/출력으로 사용한다.
    """

    # ─────────────────────────────────────────────
    # USER INPUT
    # ─────────────────────────────────────────────
    question: str
    image_path: Optional[str] = None

    # ─────────────────────────────────────────────
    # AGENT OUTPUTS
    # ─────────────────────────────────────────────
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)

    # Vision Reasoner
    vision_data: Optional[Dict[str, Any]] = None

    # Graph DB
    graph_result: Optional[List[Dict[str, Any]]] = None

    # Evidence (Graph)
    evidence_paths: Optional[Dict[str, Any]] = None

    # Web Crawlers
    crawler_data: Optional[Dict[str, Any]] = None

    # Protein Designer
    design_result: Optional[Any] = None  # Pydantic 모델 or dict

    # Structure Prediction & Rendering
    structure_result: Optional[Dict[str, Any]] = None

    # ─────────────────────────────────────────────
    # SUPERVISOR / CONTROL FLOW
    # ─────────────────────────────────────────────
    next_node: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)

    def log(self, node: str, data: Any):
        """각 노드의 결과를 reasoning trace로 기록"""
        self.history.append({"node": node, "data": data})

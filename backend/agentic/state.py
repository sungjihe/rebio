# backend/agentic/state.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class HeliconState(BaseModel):
    """
    Multi-Agent 전체 상태를 관리하는 중앙 state 모델.
    모든 노드가 이 State를 입력→출력으로 사용한다.
    """

    # --------------------------
    # USER INPUT
    # --------------------------
    question: str
    image_path: Optional[str] = None   # EntityNode 또는 API 입력

    # --------------------------
    # AGENT OUTPUTS
    # --------------------------
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)

    # Vision
    vision_data: Optional[Dict[str, Any]] = None
    image_evidence: Optional[Dict[str, Any]] = None

    # Graph DB
    graph_result: Optional[List[Dict[str, Any]]] = None

    # Evidence (Graph path)
    evidence_paths: Optional[Any] = None

    # Crawlers
    enriched_data: Optional[Dict[str, Any]] = None

    # Protein Designer
    designed_protein: Optional[Any] = None

    # Structure
    structure_result: Optional[Dict[str, Any]] = None
    structure_path: Optional[str] = None
    structure_image: Optional[str] = None

    # --------------------------
    # SUPERVISOR CONTROL FLOW
    # --------------------------
    next_node: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)

    # --------------------------
    # UTILS
    # --------------------------
    def log(self, node: str, data: Any):
        """각 노드의 내부 실행 로그를 기록"""
        self.history.append({
            "node": node,
            "data": data
        })

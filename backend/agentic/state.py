# backend/agentic/state.py

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class HeliconState(BaseModel):
    """
    Central state for all agentic nodes.
    """

    # USER INPUT
    question: str
    image_path: Optional[str] = None

    # AGENT OUTPUTS
    intent: Optional[str] = None
    entities: Dict[str, Any] = Field(default_factory=dict)

    # Vision
    vision_data: Optional[Dict[str, Any]] = None

    # Graph DB
    graph_result: Optional[List[Dict[str, Any]]] = None

    # Evidence paths
    evidence_paths: Optional[Any] = None

    # Crawler (consistency fix)
    crawler_data: Optional[Dict[str, Any]] = None   # ★ 추가됨
    enriched_data: Optional[Dict[str, Any]] = None  # 크롤링 원본

    # Protein design
    design_result: Optional[Any] = None   # ★ designed_protein → design_result
    designed_protein: Optional[Any] = None  # (backward compatibility)

    # Structure
    structure_result: Optional[Dict[str, Any]] = None
    structure_path: Optional[str] = None
    structure_image: Optional[str] = None

    # Supervisor
    next_node: Optional[str] = None
    history: List[Dict[str, Any]] = Field(default_factory=list)

    # Logging helper
    def log(self, node: str, data: Any):
        self.history.append({"node": node, "data": data})

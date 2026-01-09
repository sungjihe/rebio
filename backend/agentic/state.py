# backend/agentic/state.py


from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import time


JSONLike = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


@dataclass
class HeliconState:
    """
    Canonical HeliconState schema.
    - Keep one source of truth for each node output.
    - Provide legacy aliases for backward compatibility.
    """

    # --------------------
    # Core
    # --------------------
    question: Optional[str] = None
    intent: Optional[str] = None
    entities: Dict[str, Any] = field(default_factory=dict)

    # --------------------
    # Node outputs (canonical)
    # --------------------
    vision_data: Optional[Dict[str, Any]] = None
    graph_result: Optional[JSONLike] = None
   evidence_paths: Optional[JSONLike] = None
    enriched_data: Optional[Dict[str, Any]] = None
    designed_protein: Optional[List[Dict[str, Any]]] = None
    structure_result: Optional[Dict[str, Any]] = None
    structure_path: Optional[str] = None
    structure_image: Any = None

   reasoning_summary: Optional[str] = None
    reasoning: Optional[str] = None

   final_output: Optional[Dict[str, Any]] = None

    # --------------------
    # Orchestration
    # --------------------
    next_node: Optional[str] = None
    logs: List[Dict[str, Any]] = field(default_factory=list)

    # --------------------
    # Logging helper
    # --------------------
    def log(self, node: str, payload: Dict[str, Any]) -> None:
        self.logs.append({
            "ts": time.time(),
            "node": node,
            "payload": payload,
        })

    # =========================================================
    # Legacy aliases (do NOT store separate data, map to canonical)
    # =========================================================
    @property
    def crawler_data(self) -> Optional[Dict[str, Any]]:
        return self.enriched_data

    @crawler_data.setter
    def crawler_data(self, value: Optional[Dict[str, Any]]) -> None:
        self.enriched_data = value

    @property
    def design_result(self) -> Optional[List[Dict[str, Any]]]:
        return self.designed_protein

    @design_result.setter
    def design_result(self, value: Optional[List[Dict[str, Any]]]) -> None:
        self.designed_protein = value

    @property
    def image_path(self) -> Optional[str]:
        # Prefer entities['image_path'] as canonical.
        if isinstance(self.entities, dict):
            return self.entities.get("image_path")
        return None

    @image_path.setter
    def image_path(self, value: Optional[str]) -> None:
        if not isinstance(self.entities, dict):
            self.entities = {}
        self.entities["image_path"] = value

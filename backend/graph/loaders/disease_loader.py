# backend/graph/loaders/disease_loader.py
from typing import Dict, Any, List

from .base_loader import BaseLoader
from .utils import logger


class DiseaseLoader(BaseLoader):
    """
    :Disease 노드 로더
    기대 CSV 컬럼:
      - disease_id (MONDO/OMIM 등, 필수)
      - name
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        disease_id = (row.get("disease_id") or "").strip()
        if not disease_id:
            logger.warning("Row without disease_id skipped")
            return {}
        return {
            "disease_id": disease_id,
            "name": (row.get("name") or "").strip() or None,
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        batch = [b for b in batch if b.get("disease_id")]
        cypher = """
        UNWIND $rows AS row
        MERGE (d:Disease {disease_id: row.disease_id})
        SET d.name = coalesce(row.name, d.name)
        """
        return cypher, {"rows": batch}

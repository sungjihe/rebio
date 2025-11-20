# backend/graph/loaders/trial_loader.py

from typing import Dict, Any, List
from .base_loader import BaseLoader
from .utils import parse_date, logger


class TrialLoader(BaseLoader):
    """
    기대 CSV 컬럼:
      - nct_id
      - therapeutic_name
      - status
      - phase
      - start_date
      - why_stopped
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        nct_id = (row.get("nct_id") or "").strip()
        if not nct_id:
            logger.warning("Row without nct_id skipped")
            return {}

        return {
            "nct_id": nct_id,
            "status": (row.get("status") or "").strip() or None,
            "why_stopped": (row.get("why_stopped") or "").strip() or None,
            "phase": (row.get("phase") or "").strip() or None,
            "start_date": parse_date(row.get("start_date")),
            "therapeutic_name": (row.get("therapeutic_name") or "").strip() or None,
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]):
        batch = [b for b in batch if b.get("nct_id")]

        cypher = """
        UNWIND $rows AS row
        MERGE (t:Trial {nct_id: row.nct_id})
        SET
          t.status = coalesce(row.status, t.status),
          t.why_stopped = coalesce(row.why_stopped, t.why_stopped),
          t.phase = coalesce(row.phase, t.phase),
          t.start_date = coalesce(row.start_date, t.start_date),
          t.therapeutic_name = coalesce(row.therapeutic_name, t.therapeutic_name)
        """

        return cypher, {"rows": batch}

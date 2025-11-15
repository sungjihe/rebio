# backend/graph/loaders/drug_loader.py
from typing import Dict, Any, List

from .base_loader import BaseLoader
from .utils import parse_bool, logger


class DrugLoader(BaseLoader):
    """
    :Drug 노드 로더
    기대 CSV 컬럼:
      - drugbank_id (필수)
      - name
      - smiles
      - pubchem_cid
      - in_clinical (true/false/0/1)
      - approved (true/false/0/1)
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        drugbank_id = (row.get("drugbank_id") or "").strip()
        if not drugbank_id:
            logger.warning("Row without drugbank_id skipped")
            return {}
        return {
            "drugbank_id": drugbank_id,
            "name": (row.get("name") or "").strip() or None,
            "smiles": (row.get("smiles") or "").strip() or None,
            "pubchem_cid": (row.get("pubchem_cid") or "").strip() or None,
            "in_clinical": parse_bool(row.get("in_clinical")),
            "approved": parse_bool(row.get("approved")),
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        batch = [b for b in batch if b.get("drugbank_id")]
        cypher = """
        UNWIND $rows AS row
        MERGE (d:Drug {drugbank_id: row.drugbank_id})
        SET
          d.name = coalesce(row.name, d.name),
          d.smiles = coalesce(row.smiles, d.smiles),
          d.pubchem_cid = coalesce(row.pubchem_cid, d.pubchem_cid),
          d.in_clinical = coalesce(row.in_clinical, d.in_clinical),
          d.approved = coalesce(row.approved, d.approved)
        """
        return cypher, {"rows": batch}

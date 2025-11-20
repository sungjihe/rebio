# backend/graph/loaders/therapeutic_protein_loader.py
from typing import Dict, Any, List
from .base_loader import BaseLoader
from .utils import logger


class TherapeuticProteinLoader(BaseLoader):
    """
    기대 CSV 컬럼:
      - uniprot_id
      - drug_name
      - protein_name
      - gene
      - sequence
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        uid = (row.get("uniprot_id") or "").strip()
        if not uid:
            logger.warning("Row without uniprot_id skipped")
            return {}

        return {
            "uniprot_id": uid,
            "drug_name": (row.get("drug_name") or "").strip() or None,
            "protein_name": (row.get("protein_name") or "").strip() or None,
            "gene": (row.get("gene") or "").strip() or None,
            "sequence": (row.get("sequence") or "").strip() or None,
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]):
        batch = [b for b in batch if b.get("uniprot_id")]
        cypher = """
        UNWIND $rows AS row
        MERGE (t:TherapeuticProtein {uniprot_id: row.uniprot_id})
        SET t.drug_name = coalesce(row.drug_name, t.drug_name),
            t.protein_name = coalesce(row.protein_name, t.protein_name),
            t.gene = coalesce(row.gene, t.gene),
            t.sequence = coalesce(row.sequence, t.sequence)
        """
        return cypher, {"rows": batch}


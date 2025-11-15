# backend/graph/loaders/protein_loader.py
from typing import Dict, Any, List

from .base_loader import BaseLoader
from .utils import parse_list_str, logger


class ProteinLoader(BaseLoader):
    """
    :Protein 노드 로더
    기대 CSV 컬럼:
      - uniprot_id (필수)
      - name
      - gene
      - sequence
      - pdb_ids (예: "1ABC;2DEF")
      - embedding_id
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        uniprot_id = (row.get("uniprot_id") or "").strip()
        if not uniprot_id:
            logger.warning("Row without uniprot_id skipped")
            return {}
        return {
            "uniprot_id": uniprot_id,
            "name": (row.get("name") or "").strip() or None,
            "gene": (row.get("gene") or "").strip() or None,
            "sequence": (row.get("sequence") or "").strip() or None,
            "pdb_ids": parse_list_str(row.get("pdb_ids")),
            "embedding_id": (row.get("embedding_id") or "").strip() or None,
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        # 빈 dict (uniprot_id 없음) 제거
        batch = [b for b in batch if b.get("uniprot_id")]
        cypher = """
        UNWIND $rows AS row
        MERGE (p:Protein {uniprot_id: row.uniprot_id})
        SET
          p.name = coalesce(row.name, p.name),
          p.gene = coalesce(row.gene, p.gene),
          p.sequence = coalesce(row.sequence, p.sequence),
          p.pdb_ids = CASE
            WHEN size(row.pdb_ids) > 0 THEN row.pdb_ids
            ELSE p.pdb_ids
          END,
          p.embedding_id = coalesce(row.embedding_id, p.embedding_id)
        """
        return cypher, {"rows": batch}

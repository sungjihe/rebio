# backend/graph/loaders/publication_loader.py
from typing import Dict, Any, List

from .base_loader import BaseLoader
from .utils import parse_int, logger


class PublicationLoader(BaseLoader):
    """
    :Publication 노드 로더
    기대 CSV 컬럼:
      - pmid (필수)
      - title
      - year
      - source
    """

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        pmid = (row.get("pmid") or "").strip()
        if not pmid:
            logger.warning("Row without pmid skipped")
            return {}
        return {
            "pmid": pmid,
            "title": (row.get("title") or "").strip() or None,
            "year": parse_int(row.get("year")),
            "source": (row.get("source") or "").strip() or None,
        }

    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        batch = [b for b in batch if b.get("pmid")]
        cypher = """
        UNWIND $rows AS row
        MERGE (p:Publication {pmid: row.pmid})
        SET
          p.title = coalesce(row.title, p.title),
          p.year = coalesce(row.year, p.year),
          p.source = coalesce(row.source, p.source)
        """
        return cypher, {"rows": batch}

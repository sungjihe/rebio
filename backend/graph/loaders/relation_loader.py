# backend/graph/loaders/relation_loader.py
from typing import Dict, Any, List, Iterable

from neo4j import Driver

from .utils import (
    get_driver,
    batched,
    read_csv_dicts,
    read_jsonl_dicts,
    parse_bool,
    logger,
)


class RelationLoader:
    """
    관계(Relationship) 전용 Loader
    - Protein ~ Disease
    - Drug ~ Protein (TARGETS)
    - Drug ~ Disease (USED_FOR)
    - Trial ~ Drug / Protein
    - Publication ~ (Drug|Protein|Disease)
    - Protein ~ Protein (SIMILAR_TO)
    """

    def __init__(self, driver: Driver | None = None, batch_size: int = 500):
        self.driver = driver or get_driver()
        self.batch_size = batch_size
        self.log = logger.getChild(self.__class__.__name__)

    # -----------------------
    # 공통 내부 유틸
    # -----------------------
    def _load_generic(self, cypher: str, rows: Iterable[Dict[str, Any]]) -> None:
        with self.driver.session() as session:
            total = 0
            for batch in batched(rows, self.batch_size):
                session.execute_write(lambda tx: tx.run(cypher, rows=batch))
                total += len(batch)
        self.log.info(f"Done relations: {total}")

    # -----------------------
    # Protein - Disease
    # -----------------------
    def load_protein_disease_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - uniprot_id
          - disease_id
          - score
          - evidence_source
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MATCH (d:Disease {disease_id: row.disease_id})
        MERGE (p)-[r:ASSOCIATED_WITH]->(d)
        SET
          r.score = coalesce(toFloat(row.score), r.score),
          r.evidence_source = coalesce(row.evidence_source, r.evidence_source)
        """
        self._load_generic(cypher, rows)

    # -----------------------
    # Drug - Protein (TARGETS)
    # -----------------------
    def load_drug_targets_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - drugbank_id
          - uniprot_id
          - evidence_source
          - evidence_score
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (d:Drug {drugbank_id: row.drugbank_id})
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MERGE (d)-[r:TARGETS]->(p)
        SET
          r.evidence_source = coalesce(row.evidence_source, r.evidence_source),
          r.evidence_score = coalesce(toFloat(row.evidence_score), r.evidence_score)
        """
        self._load_generic(cypher, rows)

    # -----------------------
    # Drug - Disease (USED_FOR)
    # -----------------------
    def load_drug_disease_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - drugbank_id
          - disease_id
          - evidence_source
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (d:Drug {drugbank_id: row.drugbank_id})
        MATCH (di:Disease {disease_id: row.disease_id})
        MERGE (d)-[r:USED_FOR]->(di)
        SET
          r.evidence_source = coalesce(row.evidence_source, r.evidence_source)
        """
        self._load_generic(cypher, rows)

    # -----------------------
    # Protein - Protein (SIMILAR_TO)
    # -----------------------
    def load_protein_similarity_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - src_uniprot_id
          - tgt_uniprot_id
          - sim_score
          - method (예: 'esm2', 'foldseek')
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (p1:Protein {uniprot_id: row.src_uniprot_id})
        MATCH (p2:Protein {uniprot_id: row.tgt_uniprot_id})
        MERGE (p1)-[r:SIMILAR_TO]->(p2)
        SET
          r.sim_score = coalesce(toFloat(row.sim_score), r.sim_score),
          r.method = coalesce(row.method, r.method)
        """
        self._load_generic(cypher, rows)

    # -----------------------
    # Trial - Drug / Protein
    # -----------------------
    def load_trial_drug_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - nct_id
          - drugbank_id
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {nct_id: row.nct_id})
        MATCH (d:Drug {drugbank_id: row.drugbank_id})
        MERGE (t)-[:INVOLVES]->(d)
        """
        self._load_generic(cypher, rows)

    def load_trial_protein_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - nct_id
          - uniprot_id
        """
        rows = read_csv_dicts(path)
        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {nct_id: row.nct_id})
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MERGE (t)-[:INVOLVES_PROTEIN]->(p)
        """
        self._load_generic(cypher, rows)

    # -----------------------
    # Publication - (Drug|Protein|Disease)
    # -----------------------
    def load_publication_mentions_from_csv(self, path: str) -> None:
        """
        기대 CSV 컬럼:
          - pmid
          - target_type  (protein / drug / disease)
          - target_id    (uniprot_id / drugbank_id / disease_id)
          - context_snippet
          - confidence
        """
        rows = read_csv_dicts(path)

        def gen(rows_iter: Iterable[Dict[str, Any]]):
            for row in rows_iter:
                target_type = (row.get("target_type") or "").strip().lower()
                if target_type not in ("protein", "drug", "disease"):
                    continue
                yield row

        cypher = """
        UNWIND $rows AS row
        MATCH (p:Publication {pmid: row.pmid})
        CALL {
          WITH row
          WITH row WHERE row.target_type = 'protein'
          MATCH (t:Protein {uniprot_id: row.target_id})
          MERGE (p)-[r:MENTIONS]->(t)
          SET
            r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
            r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }
        CALL {
          WITH row
          WITH row WHERE row.target_type = 'drug'
          MATCH (t:Drug {drugbank_id: row.target_id})
          MERGE (p)-[r:MENTIONS]->(t)
          SET
            r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
            r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }
        CALL {
          WITH row
          WITH row WHERE row.target_type = 'disease'
          MATCH (t:Disease {disease_id: row.target_id})
          MERGE (p)-[r:MENTIONS]->(t)
          SET
            r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
            r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }
        """
        self._load_generic(cypher, gen(rows))

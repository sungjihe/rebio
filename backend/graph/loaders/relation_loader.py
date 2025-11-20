# backend/graph/loaders/relation_loader.py

from typing import Dict, Any, Iterable
from neo4j import Driver

from .utils import (
    get_driver,
    batched,
    read_csv_dicts,
    logger,
)


class RelationLoader:
    """
    관계(Relationship) Loader (TherapeuticProtein 버전)

    지원 관계:
    - Protein ──ASSOCIATED_WITH──> Disease
    - TherapeuticProtein ──TARGETS/BINDS_TO/MODULATES──> Protein
    - Protein ──SIMILAR_TO── Protein
    - Trial ──INVOLVES_TP──> TherapeuticProtein
    - Trial ──INVOLVES_PROTEIN──> Protein
    - Publication ──MENTIONS──> (Protein | TherapeuticProtein | Disease)
    """

    def __init__(self, driver: Driver | None = None, batch_size: int = 500):
        self.driver = driver or get_driver()
        self.batch_size = batch_size
        self.log = logger.getChild(self.__class__.__name__)

    # ------------------------------------------------------------------
    # Common utility
    # ------------------------------------------------------------------
    def _load_generic(self, cypher: str, rows: Iterable[Dict[str, Any]]):
        with self.driver.session() as session:
            total = 0
            for batch in batched(rows, self.batch_size):
                session.execute_write(lambda tx: tx.run(cypher, rows=batch))
                total += len(batch)

        self.log.info(f"[RelationLoader] Loaded {total} relations.")

    # ------------------------------------------------------------------
    # 1) Protein ──ASSOCIATED_WITH──> Disease
    # ------------------------------------------------------------------
    def load_protein_disease_from_csv(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MATCH (d:Disease {disease_id: row.disease_id})
        MERGE (p)-[r:ASSOCIATED_WITH]->(d)
        SET r.score = coalesce(toFloat(row.score), r.score),
            r.evidence_source = coalesce(row.evidence_source, r.evidence_source)
        """

        self._load_generic(cypher, rows)

    # ------------------------------------------------------------------
    # 2) TherapeuticProtein ─(TARGETS/BINDS_TO/MODULATES)→ Protein
    # ------------------------------------------------------------------
    def load_therapeutic_targets_from_csv(self, path: str):
        """
        CSV columns:
        - drug_uniprot_id
        - target_uniprot_id
        - relation   (TARGETS / BINDS_TO / MODULATES)
        """
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (tp:TherapeuticProtein {uniprot_id: row.drug_uniprot_id})
        MATCH (p:Protein {uniprot_id: row.target_uniprot_id})

        CALL {
            WITH tp, p, row WHERE row.relation = "TARGETS"
            MERGE (tp)-[:TARGETS]->(p)
        }
        CALL {
            WITH tp, p, row WHERE row.relation = "BINDS_TO"
            MERGE (tp)-[:BINDS_TO]->(p)
        }
        CALL {
            WITH tp, p, row WHERE row.relation = "MODULATES"
            MERGE (tp)-[:MODULATES]->(p)
        }
        """

        self._load_generic(cypher, rows)

    # ------------------------------------------------------------------
    # 3) Protein ──SIMILAR_TO── Protein
    # ------------------------------------------------------------------
    def load_protein_similarity_from_csv(self, path: str):
        """
        CSV columns (protein_embeddings_builder output):
        - source_uniprot
        - target_uniprot
        - similarity
        """
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (p1:Protein {uniprot_id: row.source_uniprot})
        MATCH (p2:Protein {uniprot_id: row.target_uniprot})
        MERGE (p1)-[r:SIMILAR_TO]->(p2)
        SET r.sim_score = coalesce(toFloat(row.similarity), r.sim_score),
            r.method = "esm2"
        """

        self._load_generic(cypher, rows)

    # ------------------------------------------------------------------
    # 4) Trial ──INVOLVES_TP──> TherapeuticProtein
    # ------------------------------------------------------------------
    def load_trial_therapeutic_from_csv(self, path: str):
        """
        CSV columns:
        - nct_id
        - drug_uniprot_id
        """
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {nct_id: row.nct_id})
        MATCH (tp:TherapeuticProtein {uniprot_id: row.drug_uniprot_id})
        MERGE (t)-[:INVOLVES_TP]->(tp)
        """

        self._load_generic(cypher, rows)

    # ------------------------------------------------------------------
    # 5) Trial ──INVOLVES_PROTEIN──> Protein
    # ------------------------------------------------------------------
    def load_trial_protein_from_csv(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {nct_id: row.nct_id})
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MERGE (t)-[:INVOLVES_PROTEIN]->(p)
        """

        self._load_generic(cypher, rows)

    # ------------------------------------------------------------------
    # 6) Publication mentions → Protein / TherapeuticProtein / Disease
    # ------------------------------------------------------------------
    def load_publication_mentions_from_csv(self, path: str):
        """
        CSV columns:
        - pmid
        - target_type (protein / therapeutic / disease)
        - target_id   (uniprot_id or disease_id)
        - context_snippet
        - confidence
        """
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (pub:Publication {pmid: row.pmid})

        // Protein mention
        CALL {
            WITH row, pub WHERE row.target_type = "protein"
            MATCH (p:Protein {uniprot_id: row.target_id})
            MERGE (pub)-[r:MENTIONS]->(p)
            SET r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
                r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }

        // TherapeuticProtein mention
        CALL {
            WITH row, pub WHERE row.target_type = "therapeutic"
            MATCH (tp:TherapeuticProtein {uniprot_id: row.target_id})
            MERGE (pub)-[r:MENTIONS]->(tp)
            SET r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
                r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }

        // Disease mention
        CALL {
            WITH row, pub WHERE row.target_type = "disease"
            MATCH (d:Disease {disease_id: row.target_id})
            MERGE (pub)-[r:MENTIONS]->(d)
            SET r.context_snippet = coalesce(row.context_snippet, r.context_snippet),
                r.confidence = coalesce(toFloat(row.confidence), r.confidence)
        }
        """

        self._load_generic(cypher, rows)


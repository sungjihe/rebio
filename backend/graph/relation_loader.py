# backend/graph/relation_loader.py

import csv
import logging
from pathlib import Path
from neo4j import GraphDatabase

from backend.config import Config

logger = logging.getLogger("RelationLoader")
logging.basicConfig(level=logging.INFO)


def read_csv_dicts(path: str):
    """CSV 파일을 dict 리스트로 로드"""
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


class RelationLoader:
    """
    Handles all Neo4j relationship loading via Cypher.
    Only the OpenTargets mapping is required.
    Other relations are optional.
    """

    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )
        self.log = logger

    def close(self):
        self.driver.close()

    # --------------------------------------------------------------
    # Helper generic loader
    # --------------------------------------------------------------
    def _load_generic(self, cypher: str, rows: list[dict]):
        with self.driver.session() as s:
            s.run(cypher, rows=rows)

    # --------------------------------------------------------------
    # 1) OpenTargets Protein–Disease relationships
    # --------------------------------------------------------------
    def load_protein_disease_from_csv(self, path: str):
        """
        Loads OpenTargets-derived protein_disease_relations.csv

        Expected columns:
            uniprot_id
            disease_id
            score
            source
            evidence_type
            active
        """
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MATCH (d:Disease {disease_id: row.disease_id})
        MERGE (p)-[r:ASSOCIATED_WITH]->(d)
        SET r.score         = toFloat(row.score),
            r.source        = coalesce(row.source, "OpenTargets"),
            r.evidence_type = coalesce(row.evidence_type, "OpenTargets"),
            r.active        = coalesce(row.active, "true")
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded OpenTargets relationships from {path}")

    # --------------------------------------------------------------
    # 2) Protein similarity (SIMILAR_TO)
    # --------------------------------------------------------------
    def load_protein_similarity(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (a:Protein {uniprot_id: row.source_uniprot})
        MATCH (b:Protein {uniprot_id: row.target_uniprot})
        MERGE (a)-[r:SIMILAR_TO]->(b)
        SET r.similarity = toFloat(row.similarity)
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded SIMILAR_TO from {path}")

    # --------------------------------------------------------------
    # 3) TP TARGETS Protein
    # --------------------------------------------------------------
    def load_therapeutic_targets(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (tp:TherapeuticProtein {uniprot_id: row.tp_uniprot})
        MATCH (p:Protein {uniprot_id: row.protein_uniprot})
        MERGE (tp)-[:TARGETS]->(p)
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded TP TARGETS from {path}")

    # --------------------------------------------------------------
    # 4) Trial → Protein
    # --------------------------------------------------------------
    def load_trial_protein_relations(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {trial_id: row.trial_id})
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MERGE (t)-[:INVESTIGATES]->(p)
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded Trial→Protein from {path}")

    # --------------------------------------------------------------
    # 5) Trial → TherapeuticProtein
    # --------------------------------------------------------------
    def load_trial_therapeutic_relations(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (t:Trial {trial_id: row.trial_id})
        MATCH (tp:TherapeuticProtein {uniprot_id: row.uniprot_id})
        MERGE (t)-[:USES]->(tp)
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded Trial→TherapeuticProtein from {path}")

    # --------------------------------------------------------------
    # 6) Publication → Protein
    # --------------------------------------------------------------
    def load_publication_protein_mentions(self, path: str):
        rows = read_csv_dicts(path)

        cypher = """
        UNWIND $rows AS row
        MATCH (pb:Publication {pmid: row.pmid})
        MATCH (p:Protein {uniprot_id: row.uniprot_id})
        MERGE (pb)-[:MENTIONS]->(p)
        """

        self._load_generic(cypher, rows)
        self.log.info(f"[RelationLoader] Loaded Publication→Protein from {path}")



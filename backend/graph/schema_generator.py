# backend/graph/schema_generator.py

import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

logger = logging.getLogger("schema_generator")
logging.basicConfig(level=logging.INFO)


class Neo4jSchemaGenerator:
    def __init__(self):
        if not NEO4J_URI:
            raise ValueError("NEO4J_URI is not set in .env")

        self.driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def apply_schema(self):
        cyphers = [

            # ========================================
            # Protein
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.uniprot_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.name);",
            "CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.length);",

            # ========================================
            # Disease
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (d:Disease) ON (d.name);",

            # ========================================
            # Drug
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.drugbank_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (dr:Drug) ON (dr.name);",

            # ========================================
            # Trial
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trial) REQUIRE t.nct_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (t:Trial) ON (t.phase);",

            # ========================================
            # Publication
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (p:Publication) ON (p.year);",

            # ========================================
            # Relationship Indexes
            # ========================================
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:SIMILAR_TO]-() ON (r.sim_score);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:ASSOCIATED_WITH]-() ON (r.score);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:TARGETS]-() ON (r.evidence_score);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:USED_FOR]-() ON (r.indication);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.confidence);",
        ]

        with self.driver.session() as session:
            for q in cyphers:
                logger.info(f"[Neo4j] Running: {q}")
                session.run(q)

        logger.info("🎉 All Neo4j schema applied successfully!")

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

            # ========================================
            # TherapeuticProtein
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:TherapeuticProtein) REQUIRE t.uniprot_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (t:TherapeuticProtein) ON (t.name);",

            # ========================================
            # Disease
            # ========================================
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (d:Disease) ON (d.name);",

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

            # TherapeuticProtein → Protein 관계들
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:TARGETS]-() ON (r.strength);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:BINDS_TO]-() ON (r.affinity);",
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:MODULATES]-() ON (r.effect_strength);",

            # Publication mentions confidence
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:MENTIONS]-() ON (r.confidence);",
        ]

        with self.driver.session() as session:
            for q in cyphers:
                logger.info(f"[Neo4j] Running: {q}")
                session.run(q)

        logger.info("🎉 Schema Applied Successfully!")

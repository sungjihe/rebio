import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

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
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def apply_schema(self):
        schema_queries = [

            # -------------------------
            # Node: Protein
            # -------------------------
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.uniprot_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.name);",

            # -------------------------
            # Node: Disease
            # -------------------------
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (d:Disease) ON (d.name);",

            # -------------------------
            # Node: Drug
            # -------------------------
            "CREATE CONSTRAINT IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.drugbank_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (dr:Drug) ON (dr.name);",

            # -------------------------
            # Node: Trial
            # -------------------------
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trial) REQUIRE t.nct_id IS UNIQUE;",

            # -------------------------
            # Node: Publication
            # -------------------------
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE;",

            # ------------------------------------------------
            # Relationship Indexes (⚡ 성능폭발 대폭 최적화)
            # ------------------------------------------------

            # SIMILAR_TO
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:SIMILAR_TO]-() ON (r.sim_score);",

            # ASSOCIATED_WITH
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:ASSOCIATED_WITH]-() ON (r.score);",

            # TARGETS
            "CREATE INDEX IF NOT EXISTS FOR ()-[r:TARGETS]-() ON (r.evidence_score);",
        ]

        with self.driver.session() as session:
            for query in schema_queries:
                logger.info(f"[Neo4j] Applying: {query}")
                session.run(query)

        logger.info("🎉 All Neo4j schema constraints and indexes applied successfully!")


if __name__ == "__main__":
    gen = Neo4jSchemaGenerator()
    gen.apply_schema()
    gen.close()

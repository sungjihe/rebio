# backend/graph/schema_generator.py

from neo4j import GraphDatabase
import logging
import os
from dotenv import load_dotenv

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
            # Protein
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Protein) REQUIRE p.uniprot_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.name);",

            # Disease
            "CREATE CONSTRAINT IF NOT EXISTS FOR (d:Disease) REQUIRE d.disease_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (d:Disease) ON (d.name);",

            # Drug
            "CREATE CONSTRAINT IF NOT EXISTS FOR (dr:Drug) REQUIRE dr.drugbank_id IS UNIQUE;",
            "CREATE INDEX IF NOT EXISTS FOR (dr:Drug) ON (dr.name);",

            # Trial
            "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Trial) REQUIRE t.nct_id IS UNIQUE;",

            # Publication
            "CREATE CONSTRAINT IF NOT EXISTS FOR (p:Publication) REQUIRE p.pmid IS UNIQUE;",
        ]

        with self.driver.session() as session:
            for query in schema_queries:
                logger.info(f"[Neo4j] Applying: {query}")
                session.run(query)

        logger.info("🎉 Neo4j schema applied successfully!")

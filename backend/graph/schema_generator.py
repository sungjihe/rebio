# backend/graph/schema_generator.py

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# ---------------------------------------------------------
# Load environment variables
# ---------------------------------------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(ENV_PATH)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


class SchemaGenerator:
    """
    Neo4j AuraDB 스키마 자동 생성기
    - Node Constraints
    - Indexes
    """

    def __init__(self):
        print("🔌 Connecting to Neo4j AuraDB...")
        self.driver = GraphDatabase.driver(
            NEO4J_URI, 
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )

    def close(self):
        self.driver.close()

    # ------------------------------------------------------------------
    # Constraint + Index Query Set
    # ------------------------------------------------------------------
    CONSTRAINTS = [
        # Protein
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (p:Protein)
        REQUIRE p.uniprot_id IS UNIQUE;
        """,

        # Disease
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (d:Disease)
        REQUIRE d.disease_id IS UNIQUE;
        """,

        # Drug
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (d:Drug)
        REQUIRE d.drugbank_id IS UNIQUE;
        """,

        # Trial
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (t:Trial)
        REQUIRE t.nct_id IS UNIQUE;
        """,

        # Publication
        """
        CREATE CONSTRAINT IF NOT EXISTS
        FOR (p:Publication)
        REQUIRE p.pmid IS UNIQUE;
        """,
    ]

    INDEXES = [
        # Names — lookup acceleration
        "CREATE INDEX IF NOT EXISTS FOR (p:Protein) ON (p.name);",
        "CREATE INDEX IF NOT EXISTS FOR (d:Disease) ON (d.name);",
        "CREATE INDEX IF NOT EXISTS FOR (dr:Drug) ON (dr.name);",

        # Optional: Relationship property indexes
        # Protein similarity
        """
        CREATE INDEX IF NOT EXISTS 
        FOR ()-[r:SIMILAR_TO]-() 
        ON (r.sim_score);
        """,

        # Evidence lookup
        """
        CREATE INDEX IF NOT EXISTS
        FOR ()-[r:ASSOCIATED_WITH]-()
        ON (r.score);
        """,
    ]

    # ------------------------------------------------------------------
    # Apply schema
    # ------------------------------------------------------------------
    def apply_schema(self):
        with self.driver.session() as session:
            print("\n🏗  Applying Neo4j Schema...\n")

            # Constraints
            for q in self.CONSTRAINTS:
                print(f"🛠  Applying constraint:\n{q.strip()}")
                session.run(q)

            # Indexes
            for q in self.INDEXES:
                print(f"📌 Creating index:\n{q.strip()}")
                session.run(q)

            print("\n🎉 Schema successfully applied to Neo4j AuraDB!\n")


# ---------------------------------------------------------
# Main execution
# ---------------------------------------------------------
if __name__ == "__main__":
    sg = SchemaGenerator()
    try:
        sg.apply_schema()
    finally:
        sg.close()

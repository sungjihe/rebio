# backend/graph/verify_graph_setup.py

import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

# Load .env
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)

logger = logging.getLogger("verify_graph_setup")
logging.basicConfig(level=logging.INFO)


# =====================================================
# Neo4j Setup Checker
# =====================================================
class GraphSetupVerifier:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

        if not (self.uri and self.user and self.password):
            raise ValueError("NEO4J_URI / USER / PASSWORD missing in .env")

        logger.info(f"Connecting to Neo4j → {self.uri} ({self.user})")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        if self.driver:
            self.driver.close()

    # -------------------------------------------------
    def check_connection(self):
        """Check if Neo4j connection works."""
        try:
            with self.driver.session() as s:
                res = s.run("RETURN 1 AS ok").single()
                logger.info(f"[Connection] OK → {res['ok']}")
            return True
        except Exception as e:
            logger.error(f"[Connection] FAILED: {e}")
            return False

    # -------------------------------------------------
    def check_schema(self):
        """Show constraints & indexes."""
        with self.driver.session() as s:
            constraints = s.run("SHOW CONSTRAINTS").data()
            indexes = s.run("SHOW INDEXES").data()

        logger.info("\n[Schema] Constraints:")
        for c in constraints:
            logger.info(f"  - {c.get('name')} → {c.get('description')}")

        logger.info("\n[Schema] Indexes:")
        for i in indexes:
            logger.info(f"  - {i.get('name')} → {i.get('description')}")

        return constraints, indexes

    # -------------------------------------------------
    def check_data_counts(self):
        """Count basic node & relationship types."""
        queries = {
            "Proteins": "MATCH (n:Protein) RETURN count(n) AS c",
            "Diseases": "MATCH (n:Disease) RETURN count(n) AS c",
            "Drugs": "MATCH (n:Drug) RETURN count(n) AS c",
            "Trials": "MATCH (n:Trial) RETURN count(n) AS c",
            "SIMILAR_TO": "MATCH ()-[r:SIMILAR_TO]-() RETURN count(r) AS c",
            "ASSOCIATED_WITH": "MATCH ()-[r:ASSOCIATED_WITH]-() RETURN count(r) AS c",
            "TARGETS": "MATCH ()-[r:TARGETS]-() RETURN count(r) AS c",
        }

        results = {}
        with self.driver.session() as s:
            for label, q in queries.items():
                count = s.run(q).single()["c"]
                results[label] = count
                logger.info(f"[DataCount] {label}: {count}")

        return results

    # -------------------------------------------------
    def run_test_queries(self, sample_uid="P04637"):
        """Test basic graph operations."""
        logger.info("\n[Test] Running example queries...")

        with self.driver.session() as s:
            # Test protein → similar proteins
            q1 = """
            MATCH (p:Protein {uniprot_id: $uid})-[:SIMILAR_TO]->(p2)
            RETURN p2.uniprot_id AS uid LIMIT 5
            """
            sims = s.run(q1, {"uid": sample_uid}).data()
            logger.info(f"  - Similar proteins for {sample_uid}: {sims}")

            # Test protein → diseases
            q2 = """
            MATCH (p:Protein {uniprot_id: $uid})-[:ASSOCIATED_WITH]->(d)
            RETURN d.disease_id AS d LIMIT 5
            """
            diseases = s.run(q2, {"uid": sample_uid}).data()
            logger.info(f"  - Associated diseases: {diseases}")

        return {"similar": sims, "diseases": diseases}

    # -------------------------------------------------
    def run(self):
        logger.info("\n==============================")
        logger.info("🔍 ReBio Neo4j Graph Setup Check")
        logger.info("==============================")

        self.check_connection()
        self.check_schema()
        self.check_data_counts()
        self.run_test_queries()

        logger.info("\n🎉 Finished all checks.\n")


# =====================================================
# Run as CLI
# =====================================================
if __name__ == "__main__":
    verifier = GraphSetupVerifier()
    verifier.run()
    verifier.close()

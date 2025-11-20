# backend/graph/verify_graph_setup.py

import os
import logging
from dotenv import load_dotenv
from neo4j import GraphDatabase

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)

logger = logging.getLogger("verify_graph_setup")
logging.basicConfig(level=logging.INFO)


class GraphSetupVerifier:
    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.user = os.getenv("NEO4J_USER")
        self.password = os.getenv("NEO4J_PASSWORD")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    def close(self):
        self.driver.close()

    def check_connection(self):
        try:
            with self.driver.session() as s:
                res = s.run("RETURN 1 AS ok").single()
                logger.info(f"[Connection] OK -> {res['ok']}")
            return True
        except Exception as e:
            logger.error(f"[Connection FAILED] {e}")
            return False

    def check_schema(self):
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

    def check_data_counts(self):
        queries = {
            "Proteins": "MATCH (n:Protein) RETURN count(n) AS c",
            "TherapeuticProteins": "MATCH (n:TherapeuticProtein) RETURN count(n) AS c",
            "Diseases": "MATCH (n:Disease) RETURN count(n) AS c",
            "Trials": "MATCH (n:Trial) RETURN count(n) AS c",
            "SIMILAR_TO": "MATCH ()-[r:SIMILAR_TO]-() RETURN count(r) AS c",
            "ASSOCIATED_WITH": "MATCH ()-[r:ASSOCIATED_WITH]-() RETURN count(r) AS c",
            "TARGETS": "MATCH ()-[r:TARGETS]-() RETURN count(r) AS c",
            "BINDS_TO": "MATCH ()-[r:BINDS_TO]-() RETURN count(r) AS c",
            "MODULATES": "MATCH ()-[r:MODULATES]-() RETURN count(r) AS c",
        }

        results = {}
        with self.driver.session() as s:
            for label, q in queries.items():
                count = s.run(q).single()["c"]
                results[label] = count
                logger.info(f"[DataCount] {label}: {count}")

        return results

    def run_test_queries(self, sample_uid="P04637"):
        logger.info("\n[Test Queries]")

        with self.driver.session() as s:
            sims = s.run(
                """
                MATCH (p:Protein {uniprot_id:$uid})-[:SIMILAR_TO]->(q)
                RETURN q.uniprot_id LIMIT 5
                """, {"uid": sample_uid}
            ).data()

            diseases = s.run(
                """
                MATCH (p:Protein {uniprot_id:$uid})-[:ASSOCIATED_WITH]->(d)
                RETURN d.disease_id LIMIT 5
                """, {"uid": sample_uid}
            ).data()

            ther = s.run(
                """
                MATCH (p:Protein {uniprot_id:$uid})<-[:TARGETS]-(t:TherapeuticProtein)
                RETURN t.uniprot_id LIMIT 5
                """, {"uid": sample_uid}
            ).data()

        logger.info(f"  Similar proteins: {sims}")
        logger.info(f"  Diseases: {diseases}")
        logger.info(f"  Therapeutic hits: {ther}")

        return {"similar": sims, "diseases": diseases, "therapeutics": ther}

    def run(self):
        logger.info("🔍 Verifying Graph Setup...\n")
        self.check_connection()
        self.check_schema()
        self.check_data_counts()
        self.run_test_queries()
        logger.info("\n🎉 Verification Complete.\n")


if __name__ == "__main__":
    v = GraphSetupVerifier()
    v.run()
    v.close()

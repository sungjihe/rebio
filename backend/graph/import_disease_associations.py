from neo4j import GraphDatabase
import csv
from pathlib import Path
import logging

from backend.pipeline.config import PROCESSED_DATA_ROOT
from dotenv import load_dotenv
import os

logger = logging.getLogger("import_disease_associations")
logging.basicConfig(level=logging.INFO)

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PWD = os.getenv("NEO4J_PASSWORD")

CSV_PATH = PROCESSED_DATA_ROOT / "disease_associations.csv"

def import_associations():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PWD))
    logger.info(f"[IMPORT] Reading CSV: {CSV_PATH}")

    with driver.session() as session:
        with CSV_PATH.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            count = 0
            for row in reader:
                session.run(
                    """
                    MATCH (p:Protein {uniprot_id: $uid})
                    MATCH (d:Disease {disease_id: $did})
                    MERGE (p)-[r:ASSOCIATED_WITH]->(d)
                    SET r.score = $score,
                        r.source = $source,
                        r.evidence_type = $etype,
                        r.reference = $ref,
                        r.active = $active
                    """,
                    uid=row["uniprot_id"],
                    did=row["disease_id"],
                    score=float(row["score"]),
                    source=row["source"],
                    etype=row["evidence_type"],
                    ref=row["reference"],
                    active=(row["active"] == "true"),
                )
                count += 1

            logger.info(f"[IMPORT] Inserted/Updated {count} ASSOCIATED_WITH relationships")

    driver.close()


if __name__ == "__main__":
    import_associations()

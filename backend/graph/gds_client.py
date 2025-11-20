# backend/graph/gds_client.py

import json
import logging
from pathlib import Path
from typing import List

from neo4j import GraphDatabase
from graphdatascience import GraphDataScience

from backend.config import Config

logger = logging.getLogger("GDSClient")
logging.basicConfig(level=logging.INFO)


class GDSClient:
    """
    Handles all Neo4j Graph Data Science operations:
      1) Load embeddings from JSONL
      2) Apply to Neo4j Protein nodes
      3) Project 'protein_similarity_graph'
      4) Run KNN → SIMILAR_TO relations
    """

    def __init__(self):
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USER
        self.password = Config.NEO4J_PASSWORD

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.gds = GraphDataScience(self.uri, auth=(self.user, self.password))

        logger.info(f"[GDS] Connected to Neo4j at {self.uri}")

    # -------------------------------------------------------
    # Read JSONL Embeddings
    # -------------------------------------------------------
    def load_embeddings_jsonl(self, jsonl_path: Path):
        if not jsonl_path.exists():
            raise FileNotFoundError(f"❌ Embedding JSONL not found: {jsonl_path}")

        logger.info(f"[GDS] Loading embeddings from JSONL → {jsonl_path}")

        rows = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line)
                if "id" not in obj or "embedding" not in obj:
                    continue

                rows.append({
                    "id": obj["id"],
                    "embedding": obj["embedding"],
                })

        logger.info(f"[GDS] Loaded {len(rows)} embeddings")
        return rows

    # -------------------------------------------------------
    # Write embeddings to Neo4j
    # -------------------------------------------------------
    def apply_embeddings_to_neo4j(self, rows: List[dict]):
        logger.info("[GDS] Applying embeddings to Neo4j Protein nodes...")

        query = """
        UNWIND $rows AS row
        MATCH (p:Protein {uniprot_id: row.id})
        SET p.embedding = row.embedding
        """

        with self.driver.session() as session:
            session.run(query, rows=rows)

        logger.info("[GDS] Embeddings applied to Neo4j successfully.")

    # -------------------------------------------------------
    # Build GDS Graph Projection
    # -------------------------------------------------------
    def project_graph(self):
        name = "protein_similarity_graph"

        # 이미 projection 있으면 drop
        if self.gds.graph.exists(name):
            logger.info("[GDS] Existing projection found → dropping")
            self.gds.graph.drop(name)

        logger.info("[GDS] Creating new graph projection 'protein_similarity_graph'")

        G, result = self.gds.graph.project(
            name,
            {"Protein": {"properties": ["embedding"]}},
            {},   # no relationships needed
        )

        logger.info(f"[GDS] Projection created: {result}")
        return G

    # -------------------------------------------------------
    # Run KNN to create SIMILAR_TO edges
    # -------------------------------------------------------
    def run_knn(self, G, top_k=20, cutoff=0.70):
        logger.info("[GDS] Running KNN similarity...")

        result = self.gds.knn.write(
            G,
            nodeProperties=["embedding"],
            topK=top_k,
            similarityCutoff=cutoff,
            writeRelationshipType="SIMILAR_TO",
            writeProperty="sim_score",
        )

        logger.info(f"[GDS] KNN write finished: {result}")

    # -------------------------------------------------------
    # Public entry
    # -------------------------------------------------------
    def run_similarity_pipeline(
        self,
        jsonl_path: Path = Config.PROCESSED_DATA_ROOT / "protein_embeddings.jsonl",
        top_k: int = 20,
        cutoff: float = 0.70,
    ):
        logger.info("===============================================")
        logger.info("🧬 GDS Similarity Pipeline Started")
        logger.info("===============================================")

        rows = self.load_embeddings_jsonl(jsonl_path)
        self.apply_embeddings_to_neo4j(rows)

        G = self.project_graph()
        self.run_knn(G, top_k=top_k, cutoff=cutoff)

        logger.info("🎉 GDS Similarity Pipeline Completed")


# CLI entry
if __name__ == "__main__":
    GDSClient().run_similarity_pipeline()

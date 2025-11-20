# backend/graph/gds_client.py

import json
import logging
from pathlib import Path
from typing import List, Dict

from neo4j import GraphDatabase
from graphdatascience import GraphDataScience
from backend.config import Config

logger = logging.getLogger("GDSClient")
logging.basicConfig(level=logging.INFO)


class GDSClient:
    """
    ReBio GDS Pipeline — Protein + TherapeuticProtein

    기능:
      1) 임베딩 JSONL 읽기
      2) Neo4j 노드에 embedding property 저장
      3) GDS Graph Projection 생성
      4) GDS KNN → SIMILAR_TO 관계 생성
    """

    def __init__(self):
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USER
        self.password = Config.NEO4J_PASSWORD

        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))
        self.gds = GraphDataScience(self.uri, auth=(self.user, self.password))

        logger.info(f"[GDS] Connected to Neo4j at {self.uri}")

    # ------------------------------------------------------------
    # Load JSONL embeddings
    # ------------------------------------------------------------
    def load_embeddings_jsonl(self, jsonl_path: Path) -> List[Dict]:
        if not jsonl_path.exists():
            raise FileNotFoundError(f"❌ Embedding JSONL not found: {jsonl_path}")

        logger.info(f"[GDS] Loading embeddings from {jsonl_path}")

        rows = []
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                obj = json.loads(line.strip())
                if "id" not in obj or "embedding" not in obj:
                    continue

                rows.append({
                    "id": obj["id"],
                    "embedding": obj["embedding"]
                })

        logger.info(f"[GDS] Loaded {len(rows)} embeddings")
        return rows

    # ------------------------------------------------------------
    # Apply embeddings to Neo4j nodes
    # ------------------------------------------------------------
    def apply_embeddings(self, rows: List[Dict]):
        logger.info("[GDS] Applying embeddings to Neo4j nodes...")

        query = """
        UNWIND $rows AS row
        MATCH (n)
        WHERE n.uniprot_id = row.id
        SET n.embedding = row.embedding
        """

        with self.driver.session() as s:
            s.run(query, rows=rows)

        logger.info("[GDS] Embeddings applied successfully")

    # ------------------------------------------------------------
    # Create graph projection
    # ------------------------------------------------------------
    def project_graph(self):
        name = "protein_similarity_graph"

        # Drop existing projection
        if self.gds.graph.exists(name):
            logger.info("[GDS] Dropping existing graph projection")
            self.gds.graph.drop(name)

        logger.info("[GDS] Creating graph projection 'protein_similarity_graph'")

        graph, result = self.gds.graph.project(
            name,
            {
                # BOTH labels are allowed
                "Protein": {"properties": ["embedding"]},
                "TherapeuticProtein": {"properties": ["embedding"]},
            },
            {}  # no relationships
        )

        logger.info(f"[GDS] Projection created: {result}")
        return graph

    # ------------------------------------------------------------
    # Run KNN → SIMILAR_TO relationships
    # ------------------------------------------------------------
    def run_knn(self, graph, top_k=20, cutoff=0.70):
        logger.info("[GDS] Running KNN similarity...")

        result = self.gds.knn.write(
            graph,
            nodeProperties=["embedding"],
            topK=top_k,
            similarityCutoff=cutoff,
            writeRelationshipType="SIMILAR_TO",
            writeProperty="sim_score"
        )

        logger.info(f"[GDS] KNN completed: {result}")

    # ------------------------------------------------------------
    # MASTER PIPELINE
    # ------------------------------------------------------------
    def run_similarity_pipeline(
        self,
        embeddings_jsonl: Path = Config.PROCESSED_DATA_ROOT / "protein_embeddings.jsonl",
        top_k: int = 20,
        cutoff: float = 0.70,
    ):
        logger.info("\n===============================================")
        logger.info("🧬 GDS Similarity Pipeline Started")
        logger.info("===============================================\n")

        rows = self.load_embeddings_jsonl(embeddings_jsonl)
        self.apply_embeddings(rows)

        graph = self.project_graph()
        self.run_knn(graph, top_k=top_k, cutoff=cutoff)

        logger.info("\n🎉 GDS Similarity Pipeline Completed")


if __name__ == "__main__":
    GDSClient().run_similarity_pipeline()

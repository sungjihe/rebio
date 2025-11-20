# backend/graph/gds_client_cypher.py

import json
import logging
from pathlib import Path
from typing import List, Dict

from neo4j import GraphDatabase
from backend.config import Config

logger = logging.getLogger("GDSClientCypher")
logging.basicConfig(level=logging.INFO)


class GDSClientCypher:
    """
    Cypher-based GDS Client for Neo4j Aura (Python 3.10 compatible)

    기능:
      1) 임베딩 JSONL 로드
      2) Neo4j에 embedding property 저장
      3) gds.graph.project 생성
      4) gds.knn.write 실행 → SIMILAR_TO 관계 생성
    """

    def __init__(self):
        self.uri = Config.NEO4J_URI
        self.user = Config.NEO4J_USER
        self.password = Config.NEO4J_PASSWORD

        logger.info(f"[GDS-CYPHER] Connecting to Neo4j Aura: {self.uri}")
        self.driver = GraphDatabase.driver(self.uri, auth=(self.user, self.password))

    # ------------------------------------------------------------
    # JSONL Loader
    # ------------------------------------------------------------
    def load_embeddings_jsonl(self, jsonl_path: Path) -> List[Dict]:
        if not jsonl_path.exists():
            raise FileNotFoundError(f"❌ Embeddings JSONL not found: {jsonl_path}")

        logger.info(f"[GDS-CYPHER] Loading embeddings: {jsonl_path}")

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

        logger.info(f"[GDS-CYPHER] Loaded {len(rows)} embeddings")
        return rows

    # ------------------------------------------------------------
    # Apply embedding property to nodes
    # ------------------------------------------------------------
    def apply_embeddings(self, rows: List[Dict]):
        logger.info("[GDS-CYPHER] Applying embeddings to nodes...")

        query = """
        UNWIND $rows AS row
        MATCH (n {uniprot_id: row.id})
        SET n.embedding = row.embedding
        """

        with self.driver.session() as s:
            s.run(query, rows=rows)

        logger.info("[GDS-CYPHER] Embedding properties applied")

    # ------------------------------------------------------------
    # Create GDS projection via Cypher
    # ------------------------------------------------------------
    def create_projection(self, name="protein_similarity_graph"):
        logger.info("[GDS-CYPHER] Creating GDS projection...")

        drop_query = """
        CALL gds.graph.drop($name, false)
        """

        create_query = """
        CALL gds.graph.project(
            $name,
            ['Protein', 'TherapeuticProtein'],
            [],
            {nodeProperties: ['embedding']}
        )
        YIELD graphName, nodeCount, relationshipCount
        RETURN graphName, nodeCount, relationshipCount
        """

        with self.driver.session() as s:
            # Drop existing graph if exists
            s.run(drop_query, name=name)

            # Create new projection
            result = s.run(create_query, name=name).data()
            logger.info(f"[GDS-CYPHER] Projection created: {result}")

    # ------------------------------------------------------------
    # Run KNN to generate SIMILAR_TO
    # ------------------------------------------------------------
    def run_knn(self, name="protein_similarity_graph", top_k=20, cutoff=0.70):
        logger.info("[GDS-CYPHER] Running GDS KNN...")

        query = """
        CALL gds.knn.write(
            $name,
            {
                nodeProperties: ['embedding'],
                topK: $topK,
                similarityCutoff: $cutoff,
                writeRelationshipType: 'SIMILAR_TO',
                writeProperty: 'sim_score'
            }
        )
        """

        with self.driver.session() as s:
            result = s.run(
                query,
                name=name,
                topK=top_k,
                cutoff=cutoff
            ).data()

        logger.info(f"[GDS-CYPHER] KNN result: {result}")

    # ------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------
    def run_similarity_pipeline(
        self,
        embeddings_jsonl: Path = Config.PROCESSED_DATA_ROOT / "protein_embeddings.jsonl",
        top_k: int = 20,
        cutoff: float = 0.70,
    ):
        logger.info("\n====================")
        logger.info("🧬 Cypher GDS Pipeline Started")
        logger.info("====================\n")

        rows = self.load_embeddings_jsonl(embeddings_jsonl)
        self.apply_embeddings(rows)

        self.create_projection()
        self.run_knn(top_k=top_k, cutoff=cutoff)

        logger.info("\n🎉 Cypher GDS Pipeline Completed Successfully")


if __name__ == "__main__":
    GDSClientCypher().run_similarity_pipeline()

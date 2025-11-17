# backend/graph/graph_search_client.py

import os
from typing import List, Dict, Optional, Any

from dotenv import load_dotenv
from neo4j import GraphDatabase, Driver
from neo4j.graph import Path as Neo4jPath, Node as Neo4jNode, Relationship as Neo4jRel

# .env 로드
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)


class GraphSearchClient:
    """
    Neo4j Cypher Wrapper:
    - 단백질 기반 질병 예측
    - 약물 추천
    - 유사 단백질 검색
    - Evidence Path 추출 (Protein-Disease / Protein-Drug)
    """

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI")
        self.user = user or os.getenv("NEO4J_USER")
        self.password = password or os.getenv("NEO4J_PASSWORD")

        if not (self.uri and self.user and self.password):
            raise ValueError("Neo4j 환경변수(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)가 설정되어야 합니다.")

        self.driver: Driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

    def close(self):
        if self.driver:
            self.driver.close()

    # =====================================================
    # 내부 헬퍼: 일반 쿼리 실행
    # =====================================================
    def _run(self, query: str, params: Optional[Dict[str, Any]] = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    # =====================================================
    # 내부 헬퍼: Neo4j Path → dict 변환
    # (EvidencePathNode와 완전히 동기화된 형태)
    # =====================================================
    def _path_to_dict(self, path: Neo4jPath) -> Dict[str, Any]:
        def node_to_dict(n: Neo4jNode) -> Dict[str, Any]:
            return {
                "id": n.id,
                "labels": list(n.labels),
                "properties": dict(n),
            }

        def rel_to_dict(r: Neo4jRel) -> Dict[str, Any]:
            return {
                "id": r.id,
                "type": r.type,
                "start": r.start_node.id,
                "end": r.end_node.id,
                "properties": dict(r),
            }

        return {
            "nodes": [node_to_dict(n) for n in path.nodes],
            "relationships": [rel_to_dict(r) for r in path.relationships],
        }

    # =====================================================
    # 0) Evidence Path: Protein - Disease
    # =====================================================
    def evidence_paths_protein_disease(
        self,
        uniprot_id: str,
        disease_id: str,
        max_paths: int = 5,
        max_hops: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Protein(uniprot_id) ↔ Disease(disease_id) 사이의 근거 경로 리스트
        - var-length path [*1..max_hops]
        """
        max_paths = int(max_paths)
        max_hops = int(max_hops)

        query = f"""
        MATCH (prot:Protein)
        USING INDEX prot:Protein(uniprot_id)
        WHERE prot.uniprot_id = $uniprot_id

        MATCH (dis:Disease)
        USING INDEX dis:Disease(disease_id)
        WHERE dis.disease_id = $disease_id

        MATCH p = (prot)-[*1..{max_hops}]-(dis)
        RETURN p
        LIMIT {max_paths}
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                {
                    "uniprot_id": uniprot_id,
                    "disease_id": disease_id,
                },
            )
            return [self._path_to_dict(record["p"]) for record in result]

    # =====================================================
    # 0) Evidence Path: Protein - Drug
    # =====================================================
    def evidence_paths_protein_drug(
        self,
        uniprot_id: str,
        drugbank_id: str,
        max_paths: int = 5,
        max_hops: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Protein(uniprot_id) ↔ Drug(drugbank_id) 사이의 근거 경로 리스트
        """
        max_paths = int(max_paths)
        max_hops = int(max_hops)

        query = f"""
        MATCH (prot:Protein)
        USING INDEX prot:Protein(uniprot_id)
        WHERE prot.uniprot_id = $uniprot_id

        MATCH (dr:Drug)
        USING INDEX dr:Drug(drugbank_id)
        WHERE dr.drugbank_id = $drugbank_id

        MATCH p = (prot)-[*1..{max_hops}]-(dr)
        RETURN p
        LIMIT {max_paths}
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                {
                    "uniprot_id": uniprot_id,
                    "drugbank_id": drugbank_id,
                },
            )
            return [self._path_to_dict(record["p"]) for record in result]

    # =====================================================
    # 1) 단백질 기반 질병 예측 (인덱스 최적화)
    # =====================================================
    def predict_diseases(self, uniprot_id: str, top_k: int = 20):
        """
        Protein → Disease ranking
        direct_score: (p)-[:ASSOCIATED_WITH]->(d)
        propagated_score: (p)-[:SIMILAR_TO]->(p2)-[:ASSOCIATED_WITH]->(d)
        """
        query = """
        MATCH (p:Protein)
        USING INDEX p:Protein(uniprot_id)
        WHERE p.uniprot_id = $uniprot_id

        OPTIONAL MATCH (p)-[d1:ASSOCIATED_WITH]->(d:Disease)
        OPTIONAL MATCH (p)-[s:SIMILAR_TO]->(p2:Protein)-[d2:ASSOCIATED_WITH]->(d)

        WITH
            d,
            max(coalesce(d1.score, 0.0)) AS direct_score,
            max(coalesce(s.sim_score, 0.0) * coalesce(d2.score, 1.0)) AS propagated_score,
            collect(DISTINCT p2.uniprot_id) AS support_proteins

        WHERE d IS NOT NULL

        WITH
            d,
            direct_score,
            propagated_score,
            support_proteins,
            (0.7 * direct_score + 0.3 * propagated_score) AS total_score

        RETURN
            d.disease_id AS disease_id,
            d.name AS disease_name,
            total_score,
            direct_score,
            propagated_score,
            support_proteins

        ORDER BY total_score DESC
        LIMIT $top_k
        """
        return self._run(query, {"uniprot_id": uniprot_id, "top_k": top_k})

    # =====================================================
    # 2) 약물 추천 (인덱스 최적화)
    # =====================================================
    def recommend_drugs(self, uniprot_id: str, top_k: int = 20):
        """
        Protein → Drug ranking
        direct_target_score: (dr)-[:TARGETS]->(p)
        propagated_target_score: p ~ sp (SIMILAR_TO) + (dr)-[:TARGETS]->(sp)
        """
        query = """
        MATCH (p:Protein)
        USING INDEX p:Protein(uniprot_id)
        WHERE p.uniprot_id = $uniprot_id

        OPTIONAL MATCH (dr:Drug)-[t1:TARGETS]->(p)

        OPTIONAL MATCH (p)-[s:SIMILAR_TO]->(sp:Protein)
        OPTIONAL MATCH (dr)-[t2:TARGETS]->(sp)

        OPTIONAL MATCH (dr)-[:USED_FOR]->(d:Disease)

        WITH
            dr,
            max(coalesce(t1.evidence_score, 0.0)) AS direct_target_score,
            max(coalesce(s.sim_score, 0.0) * coalesce(t2.evidence_score, 1.0)) AS propagated_target_score,
            collect(DISTINCT sp.uniprot_id) AS support_proteins,
            collect(DISTINCT d.name) AS indications

        WHERE dr IS NOT NULL

        WITH
            dr,
            direct_target_score,
            propagated_target_score,
            support_proteins,
            indications,
            (0.7 * direct_target_score + 0.3 * propagated_target_score) AS total_score

        RETURN
            dr.drugbank_id AS drugbank_id,
            dr.name AS drug_name,
            total_score,
            direct_target_score,
            propagated_target_score,
            support_proteins,
            indications

        ORDER BY total_score DESC
        LIMIT $top_k
        """
        return self._run(query, {"uniprot_id": uniprot_id, "top_k": top_k})

    # =====================================================
    # 3) 유사 단백질 검색 (인덱스 최적화)
    # =====================================================
    def similar_proteins(self, uniprot_id: str, top_k: int = 20):
        """
        Protein → similar Proteins
        """
        query = """
        MATCH (p:Protein)
        USING INDEX p:Protein(uniprot_id)
        WHERE p.uniprot_id = $uniprot_id

        MATCH (p)-[s:SIMILAR_TO]->(p2:Protein)

        RETURN
            p2.uniprot_id AS protein_id,
            coalesce(p2.name, p2.uniprot_id) AS protein_name,
            s.sim_score AS similarity

        ORDER BY similarity DESC
        LIMIT $top_k
        """
        return self._run(query, {"uniprot_id": uniprot_id, "top_k": top_k})


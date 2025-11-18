# backend/graph/graph_search_client.py

"""
GraphSearchClient
- Single unified Neo4j access layer for Helicon AI
- Provides:
    • Evidence Path Search
    • Disease Prediction
    • Drug Recommendation
    • Similar Protein Search

This version is fully integrated with backend/config.py
and safe for LangGraph async/parallel execution.
"""

from typing import List, Dict, Optional, Any
from neo4j import GraphDatabase, Driver
from neo4j.graph import Path as Neo4jPath
from pathlib import Path

from backend.config import Config


class GraphSearchClient:
    """Unified Neo4j Client for Helicon Graph reasoning."""

    def __init__(
        self,
        uri: str = Config.NEO4J_URI,
        user: str = Config.NEO4J_USER,
        password: str = Config.NEO4J_PASSWORD,
    ):
        if not (uri and user and password):
            raise ValueError("❌ Neo4j 설정이 올바르지 않습니다 (.env 확인).")

        self.uri = uri
        self.user = user
        self.password = password

        self.driver: Driver = GraphDatabase.driver(
            self.uri,
            auth=(self.user, self.password),
        )

    # -----------------------------------------------------------
    # 안전하게 종료
    # -----------------------------------------------------------
    def close(self):
        if self.driver:
            self.driver.close()

    # -----------------------------------------------------------
    # 안전한 쿼리 실행 헬퍼
    # -----------------------------------------------------------
    def _run(self, query: str, params: Optional[Dict[str, Any]] = None):
        """Run Cypher safely and return clean dict rows."""
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    # -----------------------------------------------------------
    # Neo4j Path → dict (EvidencePathNode와 동일 구조)
    # -----------------------------------------------------------
    def _path_to_dict(self, path: Neo4jPath) -> Dict[str, Any]:
        """Convert Neo4j path into Helicon Graph format."""

        def node(n):
            return {
                "id": n.id,
                "labels": list(n.labels),
                "properties": dict(n),
            }

        def rel(r):
            return {
                "id": r.id,
                "type": r.type,
                "start": r.start_node.id,
                "end": r.end_node.id,
                "properties": dict(r),
            }

        return {
            "nodes": [node(n) for n in path.nodes],
            "relationships": [rel(r) for r in path.relationships],
        }

    # -----------------------------------------------------------
    # 단일 통합 Evidence Path Search
    # -----------------------------------------------------------
    def evidence_paths(
        self,
        start_label: str,
        start_key: str,
        start_value: str,
        end_label: str,
        end_key: str,
        end_value: str,
        max_paths: int = 5,
        max_hops: int = 4,
    ) -> List[Dict[str, Any]]:
        """
        Unified evidence path search:
        MATCH (start)-[*1..N]-(end)
        """
        query = f"""
        MATCH (s:{start_label})
        USING INDEX s:{start_label}({start_key})
        WHERE s.{start_key} = $start_value

        MATCH (e:{end_label})
        USING INDEX e:{end_label}({end_key})
        WHERE e.{end_key} = $end_value

        MATCH p = (s)-[*1..{max_hops}]-(e)
        RETURN p
        LIMIT {max_paths}
        """

        with self.driver.session() as session:
            result = session.run(
                query,
                {
                    "start_value": start_value,
                    "end_value": end_value,
                },
            )
            return [self._path_to_dict(r["p"]) for r in result]

    # convenience wrappers (Helicon nodes use these)
    def evidence_paths_protein_disease(self, uniprot_id, disease_id, **kwargs):
        return self.evidence_paths(
            "Protein", "uniprot_id", uniprot_id,
            "Disease", "disease_id", disease_id,
            **kwargs,
        )

    def evidence_paths_protein_drug(self, uniprot_id, drugbank_id, **kwargs):
        return self.evidence_paths(
            "Protein", "uniprot_id", uniprot_id,
            "Drug", "drugbank_id", drugbank_id,
            **kwargs,
        )

    # -----------------------------------------------------------
    # Disease Prediction
    # -----------------------------------------------------------
    def predict_diseases(self, uniprot_id: str, top_k: int = 20):
        """Protein → Disease ranking."""
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

    # -----------------------------------------------------------
    # Drug Recommendation
    # -----------------------------------------------------------
    def recommend_drugs(self, uniprot_id: str, top_k: int = 20):
        """Protein → Drug ranking."""
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

    # -----------------------------------------------------------
    # Similar Proteins
    # -----------------------------------------------------------
    def similar_proteins(self, uniprot_id: str, top_k: int = 20):
        """Protein → Similar Proteins."""
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

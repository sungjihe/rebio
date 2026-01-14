# backend/graph/graph_search_client.py

import statistics
from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path

from backend.config import Config


class GraphSearchClient:
    """
    GraphSearchClient v3 — TherapeuticProtein 기반 그래프 탐색

    기능:
      ✔ similar_proteins()
      ✔ predict_diseases()
      ✔ recommend_therapeutics()
      ✔ evidence_paths()

    전제(스키마/로더 정렬 기준):
      - (p:Protein)-[r:ASSOCIATED_WITH]->(d:Disease) with r.score
      - (p:Protein)-[r:SIMILAR_TO]->(q:Protein) with r.sim_score
      - (tp:TherapeuticProtein)-[r:TARGETS]->(p:Protein) with r.evidence_score (or fallback)
    """

    # --------------------------
    # INIT
    # --------------------------
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD),
        )

        # weight model
        self.WEIGHTS = {
            "direct": 1.0,        # direct protein-disease
            "similarity": 0.55,   # similarity-based inference
            "therapeutic": 0.50,  # therapeutic-protein inference
            "trial": 0.40,
            "literature": 0.35,
        }

    def close(self):
        self.driver.close()

    # --------------------------
    # z-score utility
    # --------------------------
    def _zscore(self, values: List[float]) -> List[float]:
        if len(values) <= 1:
            return [0.0 for _ in values]
        mu = statistics.mean(values)
        sd = statistics.pstdev(values) or 1e-9
        return [(v - mu) / sd for v in values]

    # --------------------------
    # node key serializer (요구 스펙 3-4)
    # --------------------------
    @staticmethod
    def node_key(n: Node) -> str:
        """
        Return a stable human-meaningful identifier for a Neo4j node.
        Priority:
            uniprot_id -> disease_id -> nct_id -> pmid -> internal id
        """
        # Neo4j Node behaves like dict for properties
        return (
            n.get("uniprot_id")
            or n.get("disease_id")
            or n.get("nct_id")
            or n.get("pmid")
            or str(n.id)
        )

    # --------------------------
    # relationship score fallback
    # --------------------------
    @staticmethod
    def _rel_score(rel: Relationship, keys: List[str], default: float = 1.0) -> float:
        """
        Fetch relationship score from a list of possible property keys.
        """
        for k in keys:
            v = rel.get(k)
            if v is not None:
                try:
                    return float(v)
                except Exception:
                    pass
        return float(default)

    # ==========================
    # 1) Similar Proteins (요구 스펙 3-2)
    # ==========================
    def similar_proteins(self, uniprot_id: str, top_k: int = 20) -> List[Dict[str, Any]]:
        cypher = """
        MATCH (p:Protein {uniprot_id:$id})-[r:SIMILAR_TO]->(q:Protein)
        RETURN q.uniprot_id AS uniprot_id,
               q.name AS name,
               q.gene AS gene,
               r.sim_score AS score
        ORDER BY score DESC
        LIMIT $limit
        """
        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id, limit=top_k).data()

        raw = [float(r.get("score") or 0.0) for r in rows]
        zscores = self._zscore(raw)

        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        return rows

    # ==========================
    # 2) Disease Prediction (요구 스펙 3-1)
    # ==========================
    def predict_diseases(self, uniprot_id: str, top_k: int = 20) -> List[Dict[str, Any]]:
        cypher = """
        // Direct associations
        MATCH (p:Protein {uniprot_id:$id})-[r:ASSOCIATED_WITH]->(d:Disease)
        RETURN d.disease_id AS disease_id,
               d.name AS name,
               r.score AS raw_score,
               "direct" AS type

        UNION

        // Similarity-based associations
        MATCH (p:Protein {uniprot_id:$id})-[srel:SIMILAR_TO]->(s:Protein)-[r:ASSOCIATED_WITH]->(d:Disease)
        RETURN d.disease_id AS disease_id,
               d.name AS name,
               r.score AS raw_score,
               "similarity" AS type
        """
        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id).data()

        weighted_scores: List[float] = []
        for r in rows:
            w = float(self.WEIGHTS.get(r["type"], 0.3))
            raw_score = float(r.get("raw_score") or 0.0)
            score = raw_score * w
            r["weight"] = w
            r["final_score"] = score
            weighted_scores.append(score)

        zscores = self._zscore(weighted_scores)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ==========================
    # 3) Recommend Therapeutics (요구 스펙 3-3)
    # ==========================
    def recommend_therapeutics(self, uniprot_id: str, top_k: int = 20) -> List[Dict[str, Any]]:
        # 스펙상 "직접: (tp)-[r:TARGETS]->(p)" 만 요구되어 있으므로
        # 우선 direct만 구현하고, 필요하면 similarity 확장 가능.
        cypher = """
        MATCH (tp:TherapeuticProtein)-[r:TARGETS]->(p:Protein {uniprot_id:$id})
        RETURN tp.uniprot_id AS uniprot_id,
               tp.name AS name,
               r.evidence_score AS raw_score
        """
        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id).data()

        # evidence_score가 없을 수 있으니 fallback(현실 대응)
        for r in rows:
            if r.get("raw_score") is None:
                # 직접 Cypher에서 fallback을 쓰려면 coalesce로 가능하지만,
                # 여기서는 Python에서 안전하게 처리.
                r["raw_score"] = 1.0

        weighted_scores: List[float] = []
        for r in rows:
            w = float(self.WEIGHTS["therapeutic"])
            raw_score = float(r.get("raw_score") or 0.0)
            score = raw_score * w
            r["weight"] = w
            r["final_score"] = score
            weighted_scores.append(score)

        zscores = self._zscore(weighted_scores)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ==========================
    # 4) Evidence Paths (요구 스펙 3-4)
    # ==========================
    def evidence_paths(self, uniprot_id: str, target_id: str, max_paths: int = 5) -> List[Dict[str, Any]]:
        """
        Find short evidence paths from a Protein to a target node (Protein or Disease).
        Returns serialized node keys rather than internal Neo4j ids.
        """
        cypher = """
        MATCH p = shortestPath(
            (s:Protein {uniprot_id:$id})-[*..4]-(t)
        )
        WHERE t.disease_id = $target
           OR t.uniprot_id = $target
           OR t.nct_id = $target
           OR t.pmid = $target
        RETURN p
        LIMIT $limit
        """

        with self.driver.session() as s:
            results = s.run(
                cypher,
                id=uniprot_id,
                target=target_id,
                limit=max_paths
            ).data()

        paths: List[Dict[str, Any]] = []
        scores: List[float] = []

        for record in results:
            path: Path = record["p"]
            rels: List[Relationship] = list(path.relationships)
            nodes: List[Node] = list(path.nodes)

            # 요구사항: node_key 기반 키로 serialize
            node_keys = [self.node_key(n) for n in nodes]

            raw_strength = 0.0
            hop_penalty = 1.0 / (1.0 + len(rels))  # hop 많을수록 감점

            for rel in rels:
                t = rel.type

                if t == "ASSOCIATED_WITH":
                    sc = self._rel_score(rel, keys=["score"], default=1.0)
                    raw_strength += self.WEIGHTS["direct"] * sc

                elif t == "SIMILAR_TO":
                    sc = self._rel_score(rel, keys=["sim_score", "similarity"], default=1.0)
                    raw_strength += self.WEIGHTS["similarity"] * sc

                elif t in ("TARGETS", "BINDS_TO", "MODULATES"):
                    # 스키마가 다양할 수 있으므로 fallback 폭을 넓힘
                    sc = self._rel_score(
                        rel,
                        keys=["evidence_score", "strength", "affinity", "effect_strength"],
                        default=1.0
                    )
                    raw_strength += self.WEIGHTS["therapeutic"] * sc

                else:
                    # 기타 관계는 보수적으로 작은 가중치로 반영하거나 무시 가능
                    raw_strength += 0.0

            final = raw_strength * hop_penalty
            scores.append(final)

            paths.append({
                "path_nodes": node_keys,
                "path_str": " → ".join(node_keys),
                "raw_score": raw_strength,
                "hop_penalty": hop_penalty,
                "final_score": final,
            })

        zscores = self._zscore(scores)
        for i, p in enumerate(paths):
            p["z_score"] = zscores[i]

        paths.sort(key=lambda x: x["z_score"], reverse=True)
        return paths[:max_paths]

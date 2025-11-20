# backend/graph/graph_search_client.py

import statistics
from neo4j import GraphDatabase
from backend.config import Config


class GraphSearchClient:
    """
    GraphSearchClient v3 — TherapeuticProtein 기반 그래프 탐색

    기능:
      ✔ similar_proteins()
      ✔ predict_diseases()
      ✔ recommend_therapeutics()
      ✔ evidence_paths()

    변경사항:
      - Drug 제거
      - TherapeuticProtein 중심 그래프
      - TARGETS / BINDS_TO / MODULATES 반영
    """

    # --------------------------
    # INIT
    # --------------------------
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
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
    def _zscore(self, values):
        if len(values) <= 1:
            return [0 for _ in values]
        mu = statistics.mean(values)
        sd = statistics.pstdev(values) or 1e-9
        return [(v - mu) / sd for v in values]

    # ==========================
    # 1) Similar Proteins
    # ==========================
    def similar_proteins(self, uniprot_id, top_k=20):
        cypher = """
        MATCH (p:Protein {uniprot_id:$id})-[:SIMILAR_TO]->(q)
        RETURN q.uniprot_id AS uniprot_id,
               q.name AS name,
               q.gene AS gene,
               q.sim_score AS score
        ORDER BY score DESC
        LIMIT $k
        """
        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id, k=top_k).data()

        raw = [r["score"] for r in rows]
        zscores = self._zscore(raw)

        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        return rows

    # ==========================
    # 2) Disease Prediction
    # ==========================
    def predict_diseases(self, uniprot_id, top_k=20):
        cypher = """
        // Direct associations
        MATCH (p:Protein {uniprot_id:$id})-[:ASSOCIATED_WITH]->(d)
        RETURN d.disease_id AS disease_id,
               d.name AS name,
               r.score AS raw_score,
               "direct" AS type

        UNION

        // Similarity-based associations
        MATCH (p:Protein {uniprot_id:$id})-[:SIMILAR_TO]->(s)-[r:ASSOCIATED_WITH]->(d)
        RETURN d.disease_id AS disease_id,
               d.name AS name,
               r.score AS raw_score,
               "similarity" AS type
        """
        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id).data()

        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], 0.3)
            score = (r["raw_score"] or 1.0) * w
            r["weight"] = w
            r["final_score"] = score
            weighted.append(score)

        zscores = self._zscore(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ==========================
    # 3) Recommend Therapeutic Proteins
    # ==========================
    def recommend_therapeutics(self, uniprot_id, top_k=20):
        cypher = """
        // Direct TARGETS / BINDS_TO / MODULATES
        MATCH (p:Protein {uniprot_id:$id})<- [r:TARGETS|BINDS_TO|MODULATES] - (tp:TherapeuticProtein)
        RETURN tp.uniprot_id AS tp_id,
               tp.name AS name,
               r.evidence_score AS raw_score,
               "direct" AS type

        UNION

        // Similarity-based
        MATCH (p:Protein {uniprot_id:$id})-[:SIMILAR_TO]->(s)
              <-[r:TARGETS|BINDS_TO|MODULATES]- (tp:TherapeuticProtein)
        RETURN tp.uniprot_id AS tp_id,
               tp.name AS name,
               r.evidence_score AS raw_score,
               "similarity" AS type
        """

        with self.driver.session() as s:
            rows = s.run(cypher, id=uniprot_id).data()

        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], self.WEIGHTS["therapeutic"])
            score = (r["raw_score"] or 1.0) * w
            r["weight"] = w
            r["final_score"] = score
            weighted.append(score)

        zscores = self._zscore(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ==========================
    # 4) Evidence Paths
    # ==========================
    def evidence_paths(self, uniprot_id, target_id, max_paths=5):
        cypher = """
        MATCH p = shortestPath(
            (s:Protein {uniprot_id:$id})-[*..4]-(t)
        )
        WHERE t.disease_id = $target
              OR t.uniprot_id = $target
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

        paths = []
        scores = []

        for record in results:
            path = record["p"]
            rels = path.relationships
            nodes = [n.id for n in path.nodes]

            raw_strength = 0
            hop_penalty = 1 / (1 + len(rels))

            for rel in rels:
                t = rel.type

                if t == "ASSOCIATED_WITH":
                    raw_strength += self.WEIGHTS["direct"] * (rel.get("score") or 1.0)

                elif t == "SIMILAR_TO":
                    raw_strength += self.WEIGHTS["similarity"] * (rel.get("sim_score") or 1.0)

                elif t in ("TARGETS", "BINDS_TO", "MODULATES"):
                    raw_strength += self.WEIGHTS["therapeutic"] * (rel.get("evidence_score") or 1.0)

            final = raw_strength * hop_penalty
            scores.append(final)

            paths.append({
                "path_nodes": nodes,
                "path_str": " → ".join(nodes),
                "raw_score": raw_strength,
                "hop_penalty": hop_penalty,
                "final_score": final
            })

        zscores = self._zscore(scores)
        for i, p in enumerate(paths):
            p["z_score"] = zscores[i]

        paths.sort(key=lambda x: x["z_score"], reverse=True)
        return paths[:max_paths]

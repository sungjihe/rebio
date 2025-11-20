# backend/graph/graph_search_client.py

import statistics
from neo4j import GraphDatabase
from backend.config import Config


class GraphSearchClient:
    """
    GraphSearchClient v2 (full override)
    - similar_proteins()
    - predict_diseases()
    - recommend_drugs()
    - evidence_paths()
    
    Core Enhancements:
      ✔ Z-score normalization
      ✔ Weight model (direct > similarity > trial)
      ✔ Hop penalty (1 / (1 + hops))
      ✔ Evidence Model 2 (evidence strength scoring)
    """

    # ------------------------------
    # INIT
    # ------------------------------
    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

        # global weights
        self.WEIGHTS = {
            "direct": 1.0,
            "similarity": 0.55,
            "trial": 0.40,
            "literature": 0.35
        }

    def close(self):
        self.driver.close()

    # ================================
    # Utility: z-score normalization
    # ================================
    def _zscore_list(self, values):
        if len(values) <= 1:
            return [0 for _ in values]
        mean = statistics.mean(values)
        std = statistics.pstdev(values) or 1e-9
        return [(v - mean) / std for v in values]

    # ================================
    # 1) Similar Proteins
    # ================================
    def similar_proteins(self, uniprot_id, top_k=20):
        cypher = """
        MATCH (p:Protein {uniprot_id:$uniprot_id})-[:SIMILAR_TO]->(q)
        RETURN q.uniprot_id AS uniprot_id, q.name AS name,
               q.gene AS gene,
               q.sim_score AS score
        ORDER BY score DESC
        LIMIT $k
        """

        with self.driver.session() as s:
            rows = s.run(cypher, uniprot_id=uniprot_id, k=top_k).data()

        # z-score normalize similarity
        raw = [r["score"] for r in rows]
        zscores = self._zscore_list(raw)

        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        return rows

    # ================================
    # 2) Predict Diseases
    # ================================
    def predict_diseases(self, uniprot_id, top_k=20):
        cypher = """
        MATCH (p:Protein {uniprot_id:$uniprot_id})-[:ASSOCIATED_WITH]->(d)
        RETURN d.disease_id AS disease_id, d.name AS name,
               r.score AS raw_score,
               "direct" AS type
        UNION
        MATCH (p:Protein {uniprot_id:$uniprot_id})-[:SIMILAR_TO]->(s)-[:ASSOCIATED_WITH]->(d)
        RETURN d.disease_id AS disease_id, d.name AS name,
               r.score AS raw_score,
               "similarity" AS type
        """

        rows = []
        with self.driver.session() as s:
            rows = s.run(cypher, uniprot_id=uniprot_id).data()

        # Apply weights
        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], 0.3)
            final = r["raw_score"] * w
            weighted.append(final)
            r["weight"] = w
            r["final_score"] = final

        # z-score normalize final scores
        zscores = self._zscore_list(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ================================
    # 3) Recommend Drugs
    # ================================
    def recommend_drugs(self, uniprot_id, top_k=20):
        cypher = """
        MATCH (p:Protein {uniprot_id:$uniprot_id})<-[:TARGETS]-(d:Drug)
        RETURN d.drugbank_id AS drugbank_id, d.name AS name,
               r.evidence_score AS raw_score,
               "direct" AS type
        UNION
        MATCH (p:Protein {uniprot_id:$uniprot_id})-[:SIMILAR_TO]->(s)<-[:TARGETS]-(d)
        RETURN d.drugbank_id AS drugbank_id, d.name AS name,
               r.evidence_score AS raw_score,
               "similarity" AS type
        """

        with self.driver.session() as s:
            rows = s.run(cypher, uniprot_id=uniprot_id).data()

        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], 0.3)
            r["weight"] = w
            r["final_score"] = r["raw_score"] * w
            weighted.append(r["final_score"])

        # z-score normalization
        zscores = self._zscore_list(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # ================================
    # 4) Evidence Path (Model 2)
    # ================================
    def evidence_paths(self, uniprot_id, target_id, max_paths=5, max_hops=4):
        """
        Evidence Model 2:
          score = (sum edge_scores) * weight(type) * hop_penalty
        """
        cypher = """
        MATCH p = shortestPath((s:Protein {uniprot_id:$uniprot_id})-[*..4]-(t))
        WHERE t.disease_id = $target OR t.drugbank_id = $target
        RETURN p
        LIMIT $limit
        """

        with self.driver.session() as s:
            res = s.run(cypher, uniprot_id=uniprot_id, target=target_id, limit=max_paths).data()

        paths_output = []
        scores = []

        for record in res:
            path = record["p"]
            nodes = [n.id for n in path.nodes]
            rels = path.relationships

            raw_strength = 0
            hop_penalty = 1 / (1 + len(rels))

            for rel in rels:
                rtype = rel.type
                if rtype == "ASSOCIATED_WITH":
                    w = self.WEIGHTS["direct"]
                    raw_strength += w * (rel.get("score") or 1.0)

                elif rtype == "SIMILAR_TO":
                    w = self.WEIGHTS["similarity"]
                    raw_strength += w * (rel.get("sim_score") or 1.0)

                elif rtype == "USED_FOR" or rtype == "TARGETS":
                    w = self.WEIGHTS["similarity"]
                    raw_strength += w * 0.8

            final = raw_strength * hop_penalty
            scores.append(final)

            paths_output.append({
                "path_nodes": nodes,
                "path_str": " → ".join(nodes),
                "raw_score": raw_strength,
                "hop_penalty": hop_penalty,
                "final_score": final,
                "weight": w
            })

        # z-score normalize final score
        zscores = self._zscore_list(scores)
        for i, p in enumerate(paths_output):
            p["z_score"] = zscores[i]

        paths_output.sort(key=lambda x: x["z_score"], reverse=True)
        return paths_output[:max_paths]

# backend/graph/graph_search_client.py

import statistics
from neo4j import GraphDatabase
from backend.config import Config


class GraphSearchClient:
    """
    GraphSearchClient v3 — TherapeuticProtein 전용 버전
    - similar_proteins()
    - predict_diseases()
    - recommend_therapeutics()
    - evidence_paths()
    """

    def __init__(self):
        self.driver = GraphDatabase.driver(
            Config.NEO4J_URI,
            auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD)
        )

        # Global weight model
        self.WEIGHTS = {
            "direct": 1.0,        # Protein → Disease 직접 연결
            "similarity": 0.55,   # 유사 단백질 경유
            "therapeutic": 0.50   # 단백질 치료제 기반
        }

    def close(self):
        self.driver.close()

    # -----------------------------
    # Utility: zscore
    # -----------------------------
    def _zscore_list(self, values):
        if len(values) <= 1:
            return [0 for _ in values]
        mean = statistics.mean(values)
        std = statistics.pstdev(values) or 1e-9
        return [(v - mean) / std for v in values]

    # -----------------------------
    # 1) Similar proteins
    # -----------------------------
    def similar_proteins(self, uniprot_id, top_k=20):
        cypher = """
        MATCH (p:Protein {uniprot_id:$uniprot_id})-[:SIMILAR_TO]->(q)
        RETURN 
            q.uniprot_id AS uniprot_id,
            q.name AS name,
            q.gene AS gene,
            q.sim_score AS score
        ORDER BY score DESC
        LIMIT $k
        """

        with self.driver.session() as s:
            rows = s.run(cypher, uniprot_id=uniprot_id, k=top_k).data()

        raw = [r["score"] for r in rows]
        zscores = self._zscore_list(raw)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        return rows

    # -----------------------------
    # 2) Predict diseases
    # -----------------------------
    def predict_diseases(self, uniprot_id, top_k=20):
        cypher = """
        // direct protein → disease
        MATCH (p:Protein {uniprot_id:$uid})-[:ASSOCIATED_WITH]->(d)
        RETURN 
            d.disease_id AS disease_id,
            d.name AS name,
            r.score AS raw_score,
            "direct" AS type
        
        UNION
        
        // similarity path: P → similar → Disease
        MATCH (p:Protein {uniprot_id:$uid})-[:SIMILAR_TO]->(s)-[:ASSOCIATED_WITH]->(d)
        RETURN 
            d.disease_id AS disease_id,
            d.name AS name,
            r.score AS raw_score,
            "similarity" AS type
        """

        with self.driver.session() as s:
            rows = s.run(cypher, uid=uniprot_id).data()

        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], 0.3)
            r["weight"] = w
            r["final_score"] = r["raw_score"] * w
            weighted.append(r["final_score"])

        zscores = self._zscore_list(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # -----------------------------
    # 3) Recommend Therapeutic Proteins
    # -----------------------------
    def recommend_therapeutics(self, uniprot_id, top_k=20):
        cypher = """
        // direct binding: (TherapeuticProtein)-[:BINDS_TO]->(Protein)
        MATCH (tp:TherapeuticProtein)-[r:BINDS_TO]->(p:Protein {uniprot_id:$uid})
        RETURN 
            tp.therapeutic_id AS therapeutic_id,
            tp.name AS name,
            r.affinity AS raw_score,
            "direct" AS type

        UNION

        // similarity path: p → similar → s ← binds ← TP
        MATCH (p:Protein {uniprot_id:$uid})-[:SIMILAR_TO]->(s)<-[r:BINDS_TO]-(tp:TherapeuticProtein)
        RETURN 
            tp.therapeutic_id AS therapeutic_id,
            tp.name AS name,
            r.affinity AS raw_score,
            "similarity" AS type

        UNION

        // therapeutic → treats → diseases associated with this protein
        MATCH (p:Protein {uniprot_id:$uid})-[:ASSOCIATED_WITH]->(d)<-[:TREATS]-(tp:TherapeuticProtein)
        RETURN 
            tp.therapeutic_id AS therapeutic_id,
            tp.name AS name,
            1.0 AS raw_score,
            "therapeutic" AS type
        """

        with self.driver.session() as s:
            rows = s.run(cypher, uid=uniprot_id).data()

        weighted = []
        for r in rows:
            w = self.WEIGHTS.get(r["type"], 0.35)
            r["weight"] = w
            r["final_score"] = r["raw_score"] * w
            weighted.append(r["final_score"])

        zscores = self._zscore_list(weighted)
        for i, r in enumerate(rows):
            r["z_score"] = zscores[i]

        rows.sort(key=lambda x: x["z_score"], reverse=True)
        return rows[:top_k]

    # -----------------------------
    # 4) Evidence paths
    # -----------------------------
    def evidence_paths(self, uniprot_id, target_id, max_paths=5, max_hops=4):
        """
        Evidence model v3:
        score = sum(edge_weight * value) * hop_penalty
        """
        cypher = """
        MATCH p = shortestPath(
            (s:Protein {uniprot_id:$src})-[*..4]-
            (t)
        )
        WHERE t.disease_id = $target OR t.therapeutic_id = $target
        RETURN p
        LIMIT $limit
        """

        with self.driver.session() as s:
            res = s.run(
                cypher,
                src=uniprot_id,
                target=target_id,
                limit=max_paths
            ).data()

        paths = []
        scores = []

        for rec in res:
            path = rec["p"]
            nodes = [n.id for n in path.nodes]
            rels = path.relationships

            raw = 0
            hop_penalty = 1 / (1 + len(rels))

            for rel in rels:
                if rel.type == "ASSOCIATED_WITH":
                    raw += self.WEIGHTS["direct"] * (rel.get("score") or 1.0)

                elif rel.type == "SIMILAR_TO":
                    raw += self.WEIGHTS["similarity"] * (rel.get("sim_score") or 1.0)

                elif rel.type == "BINDS_TO":
                    raw += self.WEIGHTS["therapeutic"] * (rel.get("affinity") or 1.0)

                elif rel.type == "TREATS":
                    raw += self.WEIGHTS["therapeutic"] * 0.8

            final = raw * hop_penalty
            scores.append(final)

            paths.append({
                "path_nodes": nodes,
                "path_str": " → ".join(nodes),
                "raw_score": raw,
                "hop_penalty": hop_penalty,
                "final_score": final
            })

        # normalize
        zscores = self._zscore_list(scores)
        for i, p in enumerate(paths):
            p["z_score"] = zscores[i]

        paths.sort(key=lambda x: x["z_score"], reverse=True)
        return paths[:max_paths]


# backend/pipeline/protein_similarity_builder.py

"""
Protein Similarity Builder (ESM2 embeddings → SIMILAR_TO relations)

Creates:
    raw/protein_similarity.csv

Format:
    src_uniprot_id, tgt_uniprot_id, sim_score, method
"""

import csv
import numpy as np
from typing import List, Tuple

import chromadb

from backend.config import Config

RAW_DATA_ROOT = Config.RAW_DATA_ROOT


# -------------------------------------------------------
# Utility: l2 normalization
# -------------------------------------------------------
def l2_norm(x: np.ndarray) -> np.ndarray:
    denom = np.linalg.norm(x)
    return x / (denom + 1e-9)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    """Cosine similarity between normalized vectors."""
    return float(np.dot(a, b))


# -------------------------------------------------------
# Main Builder function
# -------------------------------------------------------
def build_protein_embeddings(
    vectordb_path=Config.VECTORDB_PROTEIN,
    raw_root=Config.RAW_DATA_ROOT,
    collection_name="protein_embeddings",
    top_k_per_protein: int = 20,
    min_score: float = 0.70,
):
    """
    Build SIMILAR_TO edges based on ESM2 embeddings stored in ChromaDB.
    """

    print("\n===============================================")
    print("🔬 Building Protein Similarity (SIMILAR_TO edges)")
    print("===============================================")

    # --------------------------------------------
    # 1. ChromaDB Load
    # --------------------------------------------
    vectordb_path = str(vectordb_path)
    print(f"📂 Loading ChromaDB Collection: {collection_name}")
    print(f"📁 VectorDB Path: {vectordb_path}")

    client = chromadb.PersistentClient(path=vectordb_path)
    col = client.get_collection(collection_name)

    # fetch ids + embeddings + metadata
    data = col.get(include=["embeddings", "metadatas", "documents"])
    ids = data["ids"]
    embeddings = np.array(data["embeddings"], dtype=np.float32)
    metas = data["metadatas"]

    print(f"🔎 Loaded {len(ids)} protein embeddings")

    # --------------------------------------------
    # 2. Normalize embeddings
    # --------------------------------------------
    print("📐 Normalizing embeddings...")
    embeddings = np.array([l2_norm(e) for e in embeddings], dtype=np.float32)

    n = len(embeddings)
    rows: List[Tuple[str, str, float]] = []

    # --------------------------------------------
    # 3. Compute similarity
    # --------------------------------------------
    print(f"🧮 Computing SIMILAR_TO edges (threshold={min_score})")

    for i in range(n):
        v1 = embeddings[i]
        src_uniprot = metas[i].get("uniprot_id", ids[i])

        sims = []

        for j in range(n):
            if i == j:
                continue

            sim_score = cosine(v1, embeddings[j])
            if sim_score >= min_score:
                tgt_uniprot = metas[j].get("uniprot_id", ids[j])
                sims.append((tgt_uniprot, sim_score))

        # 정렬 및 top-k 제한
        sims.sort(key=lambda x: x[1], reverse=True)
        sims = sims[:top_k_per_protein]

        for tgt_uniprot, sc in sims:
            rows.append((src_uniprot, tgt_uniprot, sc))

    # --------------------------------------------
    # 4. Write CSV output
    # --------------------------------------------
    out_csv = raw_root / "protein_similarity.csv"
    out_csv.parent.mkdir(parents=True, exist_ok=True)

    print(f"💾 Writing CSV → {out_csv}")

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src_uniprot_id", "tgt_uniprot_id", "sim_score", "method"])

        for src, tgt, sc in rows:
            w.writerow([src, tgt, f"{sc:.4f}", "esm2"])

    print(f"🎉 Done: {len(rows)} SIMILAR_TO edges generated.\n")

# backend/pipeline/protein_similarity_builder.py

import os
import csv
from typing import List, Tuple

import numpy as np
import chromadb

from .config import RAW_DATA_ROOT, VECTORDB_PATH

SIMILARITY_CSV = RAW_DATA_ROOT / "protein_similarity.csv"
COLLECTION_NAME = "protein_embeddings"


def l2_norm(x: np.ndarray) -> np.ndarray:
    return x / (np.linalg.norm(x) + 1e-9)


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))


def build_protein_similarity(top_k_per_protein: int = 20, min_score: float = 0.70):
    print(f"[SIM] Loading ChromaDB at {VECTORDB_PATH}")
    client = chromadb.PersistentClient(path=str(VECTORDB_PATH))
    col = client.get_collection(COLLECTION_NAME)

    data = col.get(include=["embeddings", "metadatas"])
    ids = data["ids"]
    embs = np.array(data["embeddings"], dtype=np.float32)

    print(f"[SIM] Loaded {len(ids)} ESM2 embeddings")

    # normalize
    embs = np.array([l2_norm(e) for e in embs], dtype=np.float32)
    n = len(ids)

    rows = []

    print("[SIM] computing similarities (ESM2)...")
    for i in range(n):
        sims = []
        v1 = embs[i]

        for j in range(n):
            if i == j:
                continue
            score = cosine(v1, embs[j])
            if score >= min_score:
                sims.append((j, score))

        sims.sort(key=lambda x: x[1], reverse=True)
        sims = sims[:top_k_per_protein]

        for j, s in sims:
            rows.append((ids[i], ids[j], s))

    print(f"[SIM] Writing CSV → {SIMILARITY_CSV}")
    with open(SIMILARITY_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["src_uniprot_id", "tgt_uniprot_id", "sim_score", "method"])

        for a, b, s in rows:
            w.writerow([a, b, f"{s:.4f}", "esm2"])

    print(f"[SIM] Done: {len(rows)} SIMILAR_TO edges generated.")




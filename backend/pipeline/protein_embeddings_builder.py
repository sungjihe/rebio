# backend/pipeline/protein_embeddings_builder.py

import os
import json
import torch
import pandas as pd
import numpy as np
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

from backend.config import RAW_DATA_ROOT, PROCESSED_DATA_ROOT

# =============================================================================
# 0) 환경 설정
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# JSONL (processed)
EMBED_OUTPUT = PROCESSED_DATA_ROOT / "protein_embeddings.jsonl"

# similarity.csv → RAW (Neo4j builder가 RAW에서 찾기 때문)
SIM_OUTPUT = RAW_DATA_ROOT / "protein_similarity.csv"

# ChromaDB 저장 위치
VECTORDB_PATH = BASE_DIR / "data" / "vectordb" / "proteins"
VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

# Proteins CSV (RAW)
PROTEIN_CSV = RAW_DATA_ROOT / "proteins.csv"


# =============================================================================
# 1) GPU 자동 탐지
# =============================================================================
def get_device():
    return "cuda" if torch.cuda.is_available() else "cpu"


# =============================================================================
# 2) ESM2 기반 단백질 임베딩
# =============================================================================
def load_embedding_model():
    print("🔬 Loading ESM2 embedding model...")
    model_name = "facebook/esm2_t6_8M_UR50D"
    model = SentenceTransformer(model_name, device=get_device())
    print(f"✅ Loaded model: {model_name}")
    return model


def generate_protein_embeddings():
    print(f"📄 Loading protein list: {PROTEIN_CSV}")
    df = pd.read_csv(PROTEIN_CSV)

    # 🛠️ 1) 중복 UniProt 제거 (필수)
    before = len(df)
    df = df.drop_duplicates(subset=["uniprot_id"])
    after = len(df)

    if before != after:
        print(f"⚠️ Removed {before - after} duplicated UniProt IDs")

    if "uniprot_id" not in df.columns or "sequence" not in df.columns:
        raise ValueError("❌ CSV must contain 'uniprot_id' and 'sequence' columns.")

    model = load_embedding_model()
    embeddings = []
    ids = []

    # JSONL 초기화
    if EMBED_OUTPUT.exists():
        EMBED_OUTPUT.unlink()

    print("⚙️ Generating embeddings...")
    with open(EMBED_OUTPUT, "w", encoding="utf-8") as f:
        for _, row in tqdm(df.iterrows(), total=len(df)):
            seq = row["sequence"]
            pid = row["uniprot_id"]

            emb = model.encode(seq, convert_to_numpy=True)
            embeddings.append(emb)
            ids.append(pid)

            f.write(json.dumps({"id": pid, "embedding": emb.tolist()}) + "\n")

    print(f"✅ Embeddings saved to: {EMBED_OUTPUT}")
    return ids, np.vstack(embeddings)


# =============================================================================
# 3) ChromaDB 저장
# =============================================================================
def save_to_chroma(ids, vectors):
    print(f"🗄️ Saving embeddings to ChromaDB: {VECTORDB_PATH}")

    # 🛠️ 중복 ID 완전 제거
    if len(ids) != len(set(ids)):
        print("⚠️ Fixing duplicate IDs before saving to ChromaDB...")
        unique = {}
        for i, pid in enumerate(ids):
            if pid not in unique:
                unique[pid] = vectors[i]

        ids = list(unique.keys())
        vectors = np.vstack(list(unique.values()))

    # ChromaDB 클라이언트 초기화
    client = chromadb.PersistentClient(path=str(VECTORDB_PATH))

    # 기존 collection 삭제
    try:
        client.delete_collection("proteins")
    except Exception:
        pass

    collection = client.create_collection(
        name="proteins",
        embedding_function=None
    )

    collection.add(
        ids=ids,
        embeddings=[v.tolist() for v in vectors],
        metadatas=[{"uniprot_id": pid} for pid in ids]
    )

    print("✅ ChromaDB 저장 완료")
    return collection


# =============================================================================
# 4) Protein similarity matrix 생성
# =============================================================================
def build_protein_similarity(top_k_per_protein=20, min_score=0.7):
    print("📐 Computing protein similarity matrix...")

    # JSONL에서 로드
    ids = []
    vectors = []

    with open(EMBED_OUTPUT, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            ids.append(obj["id"])
            vectors.append(np.array(obj["embedding"], dtype=np.float32))

    vectors = np.vstack(vectors)

    # 정규화 (0 division 방지)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1e-9, norms)
    vectors_norm = vectors / norms

    # cosine similarity
    sim_matrix = np.dot(vectors_norm, vectors_norm.T)

    rows = []
    print("✨ Selecting top similar proteins...")

    for i, pid in enumerate(ids):
        sims = sim_matrix[i].copy()
        sims[i] = -1  # 자기 자신 제외

        top_idx = sims.argsort()[::-1][:top_k_per_protein]

        for j in top_idx:
            score = float(sims[j])
            if score < min_score:
                continue

            # ✅ 헤더 통일: source_uniprot,target_uniprot,sim_score
            rows.append({
                "source_uniprot": pid,
                "target_uniprot": ids[j],
                "sim_score": score
            })

    df_sim = pd.DataFrame(rows, columns=["source_uniprot", "target_uniprot", "sim_score"])
    df_sim.to_csv(SIM_OUTPUT, index=False, encoding="utf-8")
    print(f"✅ Protein similarity saved: {SIM_OUTPUT}")

    return df_sim


# =============================================================================
# 5) 전체 파이프라인 실행
# =============================================================================
def run_all():
    ids, vectors = generate_protein_embeddings()
    save_to_chroma(ids, vectors)
    build_protein_similarity()
    print("🎉 Protein embedding pipeline completed.")


if __name__ == "__main__":
    run_all()



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
from chromadb.utils import embedding_functions

# =============================================================================
# 0) 환경 설정
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

PROCESSED_DIR = BASE_DIR / "data" / "processed"
EMBED_OUTPUT = PROCESSED_DIR / "protein_embeddings.jsonl"
SIM_OUTPUT = PROCESSED_DIR / "protein_similarity.csv"

VECTORDB_PATH = BASE_DIR / "data" / "vectordb" / "proteins"
VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

PROTEIN_CSV = PROCESSED_DIR / "proteins.csv"

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
    model_name = "facebook/esm2_t6_8M_UR50D"  # 중간 크기 (빠르고 정확도 좋음)
    model = SentenceTransformer(model_name, device=get_device())
    print(f"✅ Loaded model: {model_name}")
    return model


def generate_protein_embeddings():
    print(f"📄 Loading protein list: {PROTEIN_CSV}")
    df = pd.read_csv(PROTEIN_CSV)

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

            # JSONL 저장
            f.write(json.dumps({"id": pid, "embedding": emb.tolist()}) + "\n")

    print(f"✅ Embedding saved to: {EMBED_OUTPUT}")
    return ids, np.vstack(embeddings)


# =============================================================================
# 3) ChromaDB 저장
# =============================================================================
def save_to_chroma(ids, vectors):
    print(f"🗄️ Saving embeddings to ChromaDB: {VECTORDB_PATH}")

    client = chromadb.PersistentClient(path=str(VECTORDB_PATH))

    # 동일 이름 컬렉션 존재 시 삭제
    try:
        client.delete_collection("proteins")
    except:
        pass

    collection = client.create_collection(
        name="proteins",
        embedding_function=None
    )

    # Chroma batch insert
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
            vectors.append(np.array(obj["embedding"]))

    vectors = np.vstack(vectors)

    # 정규화
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    vectors_norm = vectors / norms

    # 전체 similarity matrix (cosine)
    sim_matrix = np.dot(vectors_norm, vectors_norm.T)

    rows = []
    print("✨ Selecting top similar proteins...")
    for i, pid in enumerate(ids):
        sims = sim_matrix[i]

        # 자기 자신 제외
        sims[i] = -1

        top_idx = sims.argsort()[::-1][:top_k_per_protein]

        for j in top_idx:
            score = sims[j]
            if score < min_score:
                continue

            rows.append({
                "source_uniprot": pid,
                "target_uniprot": ids[j],
                "similarity": float(score)
            })

    df_sim = pd.DataFrame(rows)
    df_sim.to_csv(SIM_OUTPUT, index=False)
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


# main 실행용
if __name__ == "__main__":
    run_all()

# backend/pipeline/step_embeddings.py

import os
from pathlib import Path

from backend.pipeline.protein_embeddings_builder import (
    generate_protein_embeddings,
    build_protein_similarity,
    save_to_chroma,
)
from dotenv import load_dotenv

# =============================================================================
# 1) 환경 변수 로드
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


# =============================================================================
# 2) Step Runner
# =============================================================================
def run():
    print("\n======================================")
    print(" 🧬 STEP: Protein Embeddings")
    print("======================================")

    print("📌 1) 단백질 임베딩 생성 시작...")
    ids, vectors = generate_protein_embeddings()

    print("\n📌 2) ChromaDB에 저장...")
    save_to_chroma(ids, vectors)

    print("\n📌 3) 유사도 행렬 계산 및 similarity CSV 생성...")
    build_protein_similarity(top_k_per_protein=20, min_score=0.70)

    print("\n✅ STEP: embeddings 완료\n")


# CLI 실행 지원
if __name__ == "__main__":
    run()


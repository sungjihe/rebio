# backend/pipeline/step_embeddings.py

import os
from pathlib import Path

from backend.pipeline.protein_embeddings_builder import (
    generate_protein_embeddings,
    save_to_chroma,
)
from backend.graph.gds_client import GDSClient
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

    print("\n📌 3) Neo4j GDS KNN 기반 SIMILAR_TO 생성...")
    GDSClient().run_similarity_pipeline()

    print("\n✅ STEP: embeddings + GDS SIMILAR_TO 완료\n")


# CLI 실행 지원
if __name__ == "__main__":
    run()

# backend/pipeline/steps/step_embeddings.py

import logging
from backend.pipeline.protein_embeddings_builder import run_all

logger = logging.getLogger("step_embeddings")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def run():
    print("\n======================================")
    print(" 🧬 STEP: embeddings (Protein Embeddings + Similarity)")
    print("======================================")

    try:
        run_all()
        print("✅ [STEP: embeddings] Completed")
    except Exception as e:
        print(f"❌ Step 'embeddings' 실패: {e}")
        raise


if __name__ == "__main__":
    run()

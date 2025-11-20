# backend/pipeline/download_all.py

import logging
from backend.pipeline.steps import (
    step_proteins,
    step_pdb,
    step_diseases,
    step_therapeutic_proteins,   # drug → therapeutic_proteins
    step_trials,
    step_publications,
    step_open_targets,            # ← LOCAL PARQUET VERSION
    step_relations,
    step_graph,
    step_embeddings,
)

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# -----------------------------------------------------------
# STEP MAP
# -----------------------------------------------------------
STEPS = {
    "proteins": step_proteins.run,
    "pdb": step_pdb.run,
    "diseases": step_diseases.run,
    "therapeutic_proteins": step_therapeutic_proteins.run,
    "trials": step_trials.run,
    "publications": step_publications.run,

    # 🔥 CHANGE: GraphQL → LOCAL PARQUET
    # 이전: step_open_targets_graphql.run → 이제 parquet 버전 호출
    "open_targets": step_open_targets.run,

    "relations": step_relations.run,
    "graph": step_graph.run,
    "embeddings": step_embeddings.run,
}


# -----------------------------------------------------------
# Helper
# -----------------------------------------------------------
def _safe_run(step_name, func):
    print("\n======================================")
    print(f" Step '{step_name}' 시작")
    print("======================================")

    try:
        func()
        print(f"✅ Step '{step_name}' 완료")
    except Exception as e:
        print(f"❌ Step '{step_name}' 실패: {e}")


# -----------------------------------------------------------
# Main
# -----------------------------------------------------------
def main():
    print("\n\n🚀 ReBio Full Pipeline START")
    print("======================================\n")

    for name, func in STEPS.items():
        _safe_run(name, func)

    print("\n======================================")
    print("🎉 ReBio Full Pipeline COMPLETED")
    print("======================================\n")


if __name__ == "__main__":
    main()

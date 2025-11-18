# backend/pipeline/download_all.py

"""
ReBio Full Data Pipeline

사용 예시:

# 전체 파이프라인 (권장)
python -m backend.pipeline.download_all

# 특정 단계만 실행 (예: 단백질 + 그래프만)
python -m backend.pipeline.download_all --step proteins
python -m backend.pipeline.download_all --step graph
"""

import argparse
import traceback

from backend.config import Config

from backend.pipeline.steps import (
    step_proteins,
    step_pdb,
    step_diseases,
    step_drugs,
    step_trials,
    step_publications,
    step_disgenet_merge,
    step_relations,
    step_graph,
    step_embeddings,
)


STEPS_ORDERED = [
    ("proteins", step_proteins.run),
    ("pdb", step_pdb.run),
    ("diseases", step_diseases.run),
    ("drugs", step_drugs.run),
    ("trials", step_trials.run),
    ("publications", step_publications.run),
    ("disgenet", step_disgenet_merge.run),
    ("relations", step_relations.run),
    ("graph", step_graph.run),
    ("embeddings", step_embeddings.run),
]


def _safe_run(name: str, func):
    try:
        print(f"\n🚀 [PIPELINE] Step '{name}' 시작")
        func()
        print(f"✅ [PIPELINE] Step '{name}' 완료")
    except Exception as e:
        print(f"❌ [PIPELINE] Step '{name}' 실패: {e}")
        traceback.print_exc()


def run_all():
    print("\n===========================================")
    print("🚀 ReBio Full Data Pipeline 시작")
    print("===========================================\n")

    print(f"📁 DATA_ROOT: {Config.DATA_ROOT}")
    print(f"🔗 Neo4j URI: {Config.NEO4J_URI}\n")

    for name, func in STEPS_ORDERED:
        _safe_run(name, func)

    print("\n===========================================")
    print("🎉 ReBio Full Data Pipeline 완료")
    print("===========================================\n")


def run_single(step_name: str):
    step_map = {name: func for name, func in STEPS_ORDERED}
    if step_name not in step_map:
        valid = ", ".join(step_map.keys())
        raise ValueError(f"Unknown step '{step_name}'. Valid steps: {valid}")

    print(f"\n🔧 ReBio Pipeline 단일 스텝 실행: {step_name}\n")
    _safe_run(step_name, step_map[step_name])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ReBio Data Pipeline Runner")
    parser.add_argument(
        "--step",
        type=str,
        help="실행할 단일 스텝 이름 (예: proteins, pdb, diseases, drugs, trials, publications, disgenet, relations, graph, embeddings)",
    )

    args = parser.parse_args()

    if args.step:
        run_single(args.step)
    else:
        run_all()

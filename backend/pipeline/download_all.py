# backend/pipeline/download_all.py

import argparse
import traceback
from backend.config import Config

from backend.pipeline.steps import (
    step_proteins,
    step_pdb,
    step_diseases,
    step_therapeutic_proteins,
    step_trials,
    step_publications,
    step_disgenet_merge,
    step_relations,
    step_graph,
    step_embeddings,
)

STEPS_ORDERED = [
    ("proteins", step_proteins.run),
    ("therapeutic_proteins", step_therapeutic_proteins.run),
    ("pdb", step_pdb.run),
    ("diseases", step_diseases.run),
    ("trials", step_trials.run),
    ("publications", step_publications.run),
    ("disgenet", step_disgenet_merge.run),
    ("relations", step_relations.run),
    ("graph", step_graph.run),
    ("embeddings", step_embeddings.run),
]


def _safe_run(name, func):
    try:
        print(f"\n🚀 Step '{name}' 시작")
        func()
        print(f"✅ Step '{name}' 완료")
    except Exception as e:
        print(f"❌ Step '{name}' 실패: {e}")
        traceback.print_exc()


def run_all():
    print("🚀 Running Full Pipeline...\n")

    for name, func in STEPS_ORDERED:
        _safe_run(name, func)

    print("\n🎉 Pipeline Complete.\n")


def run_single(step_name):
    step_map = {name: func for name, func in STEPS_ORDERED}
    if step_name not in step_map:
        valid = ", ".join(step_map.keys())
        raise ValueError(f"Unknown step '{step_name}'. Valid: {valid}")

    _safe_run(step_name, step_map[step_name])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=str)
    args = parser.parse_args()

    if args.step:
        run_single(args.step)
    else:
        run_all()

# backend/pipeline/steps/step_relations.py

import logging
import pandas as pd
from backend.config import Config

logger = logging.getLogger("step_relations")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

RAW = Config.RAW_DATA_ROOT
PROC = Config.PROCESSED_DATA_ROOT

INPUT_CSV = PROC / "disease_associations.csv"     # from Open Targets
OUTPUT_REL = RAW / "protein_disease_relations.csv"

REQUIRED_COLS = [
    "uniprot_id",
    "disease_id",
    "score",
    "source",
    "evidence_type",
    "active",
]


def run():
    print("\n======================================")
    print(" 🔗 STEP: relations (Open Targets Only)")
    print("======================================")

    if not INPUT_CSV.exists():
        print(f"⚠️ [relations] {INPUT_CSV} 없음 → protein_disease_relations 생략")
        return

    df = pd.read_csv(INPUT_CSV)

    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"❌ [relations] Missing columns in {INPUT_CSV}: {missing}")

    rel = df[REQUIRED_COLS].copy()

    OUTPUT_REL.parent.mkdir(parents=True, exist_ok=True)
    rel.to_csv(OUTPUT_REL, index=False, encoding="utf-8")

    print(f"✅ protein_disease_relations.csv 저장 완료 → {OUTPUT_REL}")

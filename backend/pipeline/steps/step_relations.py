# backend/pipeline/steps/step_relations.py

import logging
from backend.config import Config
import pandas as pd

logger = logging.getLogger("step_relations")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

RAW = Config.RAW_DATA_ROOT
PROC = Config.PROCESSED_DATA_ROOT

INPUT_CSV = PROC / "disease_associations.csv"     # from Open Targets
OUTPUT_REL = RAW / "protein_disease_relations.csv"


def run():
    print("\n======================================")
    print(" 🔗 STEP: relations (Open Targets Only)")
    print("======================================")

    if not INPUT_CSV.exists():
        print(f"⚠️ [relations] {INPUT_CSV} 없음 → protein_disease_relations 생략")
        return

    df = pd.read_csv(INPUT_CSV)

    # RelationLoader가 기대하는 컬럼만 선택해서 그대로 사용
    rel = df[[
        "uniprot_id",
        "disease_id",
        "score",
        "source",
        "evidence_type",
        "active",
    ]].copy()

    OUTPUT_REL.parent.mkdir(parents=True, exist_ok=True)
    rel.to_csv(OUTPUT_REL, index=False)

    print(f"✅ protein_disease_relations.csv 저장 완료 → {OUTPUT_REL}")


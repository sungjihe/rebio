# backend/pipeline/steps/step_relations.py

"""
Processed 데이터 → Neo4j 관계 CSV 생성

현재 구현:
- disease_associations.csv → protein_disease_relations.csv

나중에 확장:
- drug ↔ protein (TARGETS)
- drug ↔ disease (USED_FOR)
- trial ↔ drug / protein
- publication ↔ (drug/protein/disease)
"""

import csv
from pathlib import Path

from backend.config import Config


def _build_protein_disease_relations():
    processed = Config.PROCESSED_DATA_ROOT / "disease_associations.csv"
    out_csv = Config.RAW_DATA_ROOT / "protein_disease_relations.csv"

    if not processed.exists():
        print(f"⚠️ [relations] {processed} 가 없어 protein_disease_relations 를 만들 수 없습니다.")
        return

    out_csv.parent.mkdir(parents=True, exist_ok=True)

    with processed.open("r", encoding="utf-8") as f_in, out_csv.open(
        "w", encoding="utf-8", newline=""
    ) as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)
        writer.writerow(["uniprot_id", "disease_id", "score", "evidence_source"])

        count = 0
        for row in reader:
            uid = (row.get("uniprot_id") or "").strip()
            did = (row.get("disease_id") or "").strip()
            score = (row.get("score") or "").strip()
            source = (row.get("source") or "").strip() or "DisGeNET"

            if not uid or not did:
                continue

            writer.writerow([uid, did, score or "1.0", source])
            count += 1

    print(f"✅ [relations] protein_disease_relations.csv 생성 ({count} rows) → {out_csv}")


def run():
    print("🔗 [STEP: relations] 관계 CSV 생성 시작")
    _build_protein_disease_relations()
    print("✅ [STEP: relations] 완료 (현재는 protein–disease만 생성)")

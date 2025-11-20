# backend/pipeline/steps/step_therapeutic_proteins.py

import csv
import logging
from pathlib import Path

from backend.config import Config

logger = logging.getLogger("step_therapeutic_proteins")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

RAW = Config.RAW_DATA_ROOT
TP_CSV = RAW / "therapeutic_proteins.csv"

# ============================================================
# 1) 치료용 단백질 목록 (ReBio 내부 사전 정의)
#    - UniProt 기반
#    - 이름 + 타입(Optional)
# ============================================================
THERAPEUTIC_PROTEINS = [
    {"uniprot_id": "P01579", "name": "Interferon beta-1a", "type": "cytokine"},
    {"uniprot_id": "P01563", "name": "Interferon alpha-2b", "type": "cytokine"},
    {"uniprot_id": "P05121", "name": "Erythropoietin (EPO)", "type": "hormone"},
    {"uniprot_id": "P01215", "name": "Insulin", "type": "hormone"},
    {"uniprot_id": "P01308", "name": "Proinsulin", "type": "hormone"},
    {"uniprot_id": "P02763", "name": "Alpha-1-acid glycoprotein", "type": "carrier"},
    {"uniprot_id": "P02768", "name": "Serotransferrin", "type": "carrier"},
    {"uniprot_id": "P02787", "name": "Serum albumin", "type": "carrier"},
    {"uniprot_id": "P00450", "name": "Ceruloplasmin", "type": "enzyme"},
    {"uniprot_id": "P68871", "name": "Hemoglobin subunit beta", "type": "carrier"},
    # 필요하면 계속 확장 가능
]

# ============================================================
# 2) CSV 생성 로직
# ============================================================
def run():
    print("\n======================================")
    print(" 🧬 STEP: therapeutic_proteins")
    print("======================================")

    TP_CSV.parent.mkdir(parents=True, exist_ok=True)

    with open(TP_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["uniprot_id", "name", "type"])

        for item in THERAPEUTIC_PROTEINS:
            writer.writerow([
                item["uniprot_id"],
                item["name"],
                item.get("type", "")
            ])

    print(f"✅ therapeutic_proteins.csv 저장 완료 → {TP_CSV}")


if __name__ == "__main__":
    run()

# backend/pipeline/steps/step_relations.py

import csv
from pathlib import Path
from backend.config import Config


# =============================================================================
# 1) Protein → Disease (DisGeNET 기반)
# =============================================================================
def _build_protein_disease_relations():
    src = Config.PROCESSED_DATA_ROOT / "disease_associations.csv"
    out = Config.RAW_DATA_ROOT / "protein_disease_relations.csv"

    if not src.exists():
        print(f"⚠️ [relations] {src} 없음 → protein_disease_relations 생략")
        return

    with src.open("r", encoding="utf-8") as f_in, out.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)

        writer.writerow(["uniprot_id", "disease_id", "score", "evidence_source"])

        count = 0
        for row in reader:
            uid = (row.get("uniprot_id") or "").strip()
            did = (row.get("disease_id") or "").strip()
            score = (row.get("score") or "1.0").strip()
            src_name = (row.get("source") or "DisGeNET").strip()

            if uid and did:
                writer.writerow([uid, did, score, src_name])
                count += 1

    print(f"✅ [relations] protein_disease_relations.csv 생성 ({count} rows)")


# =============================================================================
# 2) TherapeuticProtein → Protein 관계 (TARGETS / BINDS_TO / MODULATES)
# =============================================================================
def _build_therapeutic_targets():
    """
    필요 CSV: processed/therapeutic_targets_source.csv
    컬럼:
        - drug_uniprot_id
        - target_uniprot_id
        - relation (TARGETS / BINDS_TO / MODULATES)
    """
    src = Config.PROCESSED_DATA_ROOT / "therapeutic_targets_source.csv"
    out = Config.RAW_DATA_ROOT / "therapeutic_targets.csv"

    if not src.exists():
        print(f"⚠️ [relations] {src} 없음 → therapeutic_targets 생략")
        return

    with src.open("r", encoding="utf-8") as f_in, out.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)

        writer.writerow(["drug_uniprot_id", "target_uniprot_id", "relation"])

        count = 0
        for row in reader:
            d_uid = (row.get("drug_uniprot_id") or "").strip()
            t_uid = (row.get("target_uniprot_id") or "").strip()
            rel = (row.get("relation") or "").strip().upper()

            if d_uid and t_uid and rel in ("TARGETS", "BINDS_TO", "MODULATES"):
                writer.writerow([d_uid, t_uid, rel])
                count += 1

    print(f"✅ [relations] therapeutic_targets.csv 생성 ({count} rows)")


# =============================================================================
# 3) Trial → TherapeuticProtein
# =============================================================================
def _build_trial_therapeutic():
    src = Config.PROCESSED_DATA_ROOT / "trial_therapeutic_source.csv"
    out = Config.RAW_DATA_ROOT / "trial_therapeutic_relations.csv"

    if not src.exists():
        print(f"⚠️ [relations] {src} 없음 → trial_therapeutic_relations 생략")
        return

    with src.open("r", encoding="utf-8") as f_in, out.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)

        writer.writerow(["nct_id", "drug_uniprot_id"])

        count = 0
        for row in reader:
            nct = (row.get("nct_id") or "").strip()
            d_uid = (row.get("drug_uniprot_id") or "").strip()

            if nct and d_uid:
                writer.writerow([nct, d_uid])
                count += 1

    print(f"✅ [relations] trial_therapeutic_relations.csv 생성 ({count} rows)")


# =============================================================================
# 4) Trial → Protein
# =============================================================================
def _build_trial_protein():
    src = Config.PROCESSED_DATA_ROOT / "trial_protein_source.csv"
    out = Config.RAW_DATA_ROOT / "trial_protein_relations.csv"

    if not src.exists():
        print(f"⚠️ [relations] {src} 없음 → trial_protein_relations 생략")
        return

    with src.open("r", encoding="utf-8") as f_in, out.open("w", newline="", encoding="utf-8") as f_out:
        reader = csv.DictReader(f_in)
        writer = csv.writer(f_out)

        writer.writerow(["nct_id", "uniprot_id"])

        count = 0
        for row in reader:
            nct = (row.get("nct_id") or "").strip()
            uid = (row.get("uniprot_id") or "").strip()

            if nct and uid:
                writer.writerow([nct, uid])
                count += 1

    print(f"✅ [relations] trial_protein_relations.csv 생성 ({count} rows)")


# =============================================================================
# MAIN run()
# =============================================================================
def run():
    print("\n🔗 [STEP: relations] 관계 CSV 생성 시작")

    _build_protein_disease_relations()
    _build_therapeutic_targets()
    _build_trial_therapeutic()
    _build_trial_protein()

    print("✅ [STEP: relations] 완료")


if __name__ == "__main__":
    run()

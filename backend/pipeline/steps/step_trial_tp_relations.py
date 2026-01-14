# backend/pipeline/steps/step_trial_tp_relations.py

import pandas as pd
from backend.config import Config

OUTPUT = Config.RAW_DATA_ROOT / "trial_therapeutic_relations.csv"

def run():
    print("\n======================================")
    print(" 🧬 STEP: trial_tp_relations (Trial → TherapeuticProtein)")
    print("======================================")

    trials_path = Config.RAW_DATA_ROOT / "trials.csv"
    tp_path = Config.RAW_DATA_ROOT / "therapeutic_proteins.csv"

    if not trials_path.exists() or not tp_path.exists():
        print("⚠️ Missing required files. Skipping trial→therapeutic relations.")
        return

    df_trials = pd.read_csv(trials_path)
    df_tp = pd.read_csv(tp_path)

    # 필수 컬럼 체크
    for c in ["nct_id", "therapeutic_name"]:
        if c not in df_trials.columns:
            raise ValueError(f"❌ trials.csv missing column: {c}")
    for c in ["uniprot_id", "name"]:
        if c not in df_tp.columns:
            raise ValueError(f"❌ therapeutic_proteins.csv missing column: {c}")

    # 표준화
    df_trials["therapeutic_name"] = df_trials["therapeutic_name"].astype(str).str.upper()
    df_tp["name"] = df_tp["name"].astype(str).str.upper()

    relations = []

    # exact 포함 매칭: (trial therapeutic_name) 이 (tp name) 에 포함되는지
    for _, t in df_trials.iterrows():
        therapy = t["therapeutic_name"]
        nct_id = t["nct_id"]

        matches = df_tp[df_tp["name"].str.contains(therapy, na=False)]
        for _, tp in matches.iterrows():
            relations.append({
                "nct_id": nct_id,
                "tp_uniprot": tp["uniprot_id"]
            })

    if not relations:
        print("⚠️ No Trial → TherapeuticProtein matches found")
        return

    df_out = pd.DataFrame(relations, columns=["nct_id", "tp_uniprot"])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(OUTPUT, index=False, encoding="utf-8")

    print(f"✅ Saved: {OUTPUT}")


if __name__ == "__main__":
    run()

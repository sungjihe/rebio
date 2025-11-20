# backend/pipeline/steps/step_trial_tp_relations.py

import pandas as pd
from backend.config import Config
from pathlib import Path

OUTPUT = Config.RAW_DATA_ROOT / "trial_therapeutic_relations.csv"

def run():
    print("\n======================================")
    print(" 🧬 STEP: trial_therapeutic_relations")
    print("======================================")

    trials_path = Config.RAW_DATA_ROOT / "trials.csv"
    tp_path = Config.RAW_DATA_ROOT / "therapeutic_proteins.csv"

    if not trials_path.exists() or not tp_path.exists():
        print("⚠️ Missing required files. Skipping trial→therapeutic relations.")
        return

    df_trials = pd.read_csv(trials_path)
    df_tp = pd.read_csv(tp_path)

    # 표준화
    df_trials["therapeutic_name"] = df_trials["therapeutic_name"].astype(str).str.upper()
    df_tp["name"] = df_tp["name"].astype(str).str.upper()

    relations = []

    # 간단한 exact match (hybrid fuzzy match도 추가 가능)
    for _, t in df_trials.iterrows():
        therapy = t["therapeutic_name"]
        nct_id = t["nct_id"]

        # therapy 이름이 TP 이름에 포함되면 match
        matches = df_tp[df_tp["name"].str.contains(therapy, na=False)]

        for _, tp in matches.iterrows():
            relations.append({
                "nct_id": nct_id,
                "therapeutic_name": therapy,
                "tp_uniprot": tp["uniprot_id"]
            })

    if not relations:
        print("⚠️ No Trial → TherapeuticProtein matches found")
        return

    df_out = pd.DataFrame(relations)
    df_out.to_csv(OUTPUT, index=False)

    print(f"✅ Saved: {OUTPUT}")


if __name__ == "__main__":
    run()

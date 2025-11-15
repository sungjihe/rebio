# backend/graph/load_all.py
import argparse
import os
from pathlib import Path

from .loaders import (
    get_driver,
    close_driver,
    ProteinLoader,
    DiseaseLoader,
    DrugLoader,
    TrialLoader,
    PublicationLoader,
    RelationLoader,
)


def main():
    parser = argparse.ArgumentParser(description="Production-ready GraphDB Loader")
    parser.add_argument(
        "--data-root",
        type=str,
        default="./data/raw",
        help="CSV/JSONL가 들어있는 기본 폴더 경로",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        help="특정 단계만 실행 (protein,disease,drug,trial,publication,relations)",
    )
    args = parser.parse_args()

    data_root = Path(args.data_root).resolve()
    print(f"[INFO] Data root: {data_root}")

    driver = get_driver()

    try:
        # ----------------- Protein -----------------
        if not args.only or "protein" in args.only:
            protein_csv = data_root / "proteins.csv"
            if protein_csv.exists():
                print(f"[INFO] Loading Proteins from {protein_csv}")
                ProteinLoader(driver=driver).load_from_csv(str(protein_csv))
            else:
                print(f"[WARN] Protein CSV not found: {protein_csv}")

        # ----------------- Disease -----------------
        if not args.only or "disease" in args.only:
            disease_csv = data_root / "diseases.csv"
            if disease_csv.exists():
                print(f"[INFO] Loading Diseases from {disease_csv}")
                DiseaseLoader(driver=driver).load_from_csv(str(disease_csv))
            else:
                print(f"[WARN] Disease CSV not found: {disease_csv}")

        # ----------------- Drug -----------------
        if not args.only or "drug" in args.only:
            drug_csv = data_root / "drugs.csv"
            if drug_csv.exists():
                print(f"[INFO] Loading Drugs from {drug_csv}")
                DrugLoader(driver=driver).load_from_csv(str(drug_csv))
            else:
                print(f"[WARN] Drug CSV not found: {drug_csv}")

        # ----------------- Trial -----------------
        if not args.only or "trial" in args.only:
            trial_csv = data_root / "trials.csv"
            if trial_csv.exists():
                print(f"[INFO] Loading Trials from {trial_csv}")
                TrialLoader(driver=driver).load_from_csv(str(trial_csv))
            else:
                print(f"[WARN] Trial CSV not found: {trial_csv}")

        # ----------------- Publication -----------------
        if not args.only or "publication" in args.only:
            pub_csv = data_root / "publications.csv"
            if pub_csv.exists():
                print(f"[INFO] Loading Publications from {pub_csv}")
                PublicationLoader(driver=driver).load_from_csv(str(pub_csv))
            else:
                print(f"[WARN] Publication CSV not found: {pub_csv}")

        # ----------------- Relations -----------------
        if not args.only or "relations" in args.only:
            rloader = RelationLoader(driver=driver)

            # Protein-Disease
            pd_csv = data_root / "protein_disease_relations.csv"
            if pd_csv.exists():
                print(f"[INFO] Loading Protein-Disease relations from {pd_csv}")
                rloader.load_protein_disease_from_csv(str(pd_csv))

            # Drug-Protein TARGETS
            dp_csv = data_root / "drug_targets.csv"
            if dp_csv.exists():
                print(f"[INFO] Loading Drug-Protein TARGETS relations from {dp_csv}")
                rloader.load_drug_targets_from_csv(str(dp_csv))

            # Drug-Disease USED_FOR
            dd_csv = data_root / "drug_disease_relations.csv"
            if dd_csv.exists():
                print(f"[INFO] Loading Drug-Disease USED_FOR relations from {dd_csv}")
                rloader.load_drug_disease_from_csv(str(dd_csv))

            # Protein-Protein SIMILAR_TO
            pp_csv = data_root / "protein_similarity.csv"
            if pp_csv.exists():
                print(f"[INFO] Loading Protein-Protein SIMILAR_TO relations from {pp_csv}")
                rloader.load_protein_similarity_from_csv(str(pp_csv))

            # Trial-Drug
            td_csv = data_root / "trial_drug_relations.csv"
            if td_csv.exists():
                print(f"[INFO] Loading Trial-Drug relations from {td_csv}")
                rloader.load_trial_drug_from_csv(str(td_csv))

            # Trial-Protein
            tp_csv = data_root / "trial_protein_relations.csv"
            if tp_csv.exists():
                print(f"[INFO] Loading Trial-Protein relations from {tp_csv}")
                rloader.load_trial_protein_from_csv(str(tp_csv))

            # Publication-Mentions
            pm_csv = data_root / "publication_mentions.csv"
            if pm_csv.exists():
                print(f"[INFO] Loading Publication-MENTIONS relations from {pm_csv}")
                rloader.load_publication_mentions_from_csv(str(pm_csv))

    finally:
        close_driver()


if __name__ == "__main__":
    main()

# backend/graph/builder.py

"""
Full Neo4j Graph Builder for ReBio / Helicon
- Reads CSVs from Config.RAW_DATA_ROOT
- Creates nodes: Protein, Disease, Drug, Trial, Publication
- Creates relations: ASSOCIATED_WITH, TARGETS, USED_FOR, SIMILAR_TO, etc.
"""

from pathlib import Path
import traceback

from backend.config import Config
from backend.graph.loaders import (
    get_driver,
    close_driver,
    ProteinLoader,
    DiseaseLoader,
    DrugLoader,
    TrialLoader,
    PublicationLoader,
    RelationLoader,
)


def _safe_load(name: str, func, *args):
    try:
        print(f"\n🚀 [{name}] 시작")
        func(*args)
        print(f"✅ [{name}] 완료")
    except Exception as e:
        print(f"❌ [{name}] 실패: {e}")
        traceback.print_exc()


def build_full_graph(data_root: Path | str | None = None):
    """
    ReBio 전체 그래프를 Neo4j에 로딩.
    - data_root가 None이면 Config.RAW_DATA_ROOT 사용
    - CSV가 없으면 경고만 찍고 스킵
    """
    if data_root is None:
        data_root = Config.RAW_DATA_ROOT
    data_root = Path(data_root)

    print("\n===============================================")
    print("🧬 ReBio GraphDB Builder")
    print("===============================================")
    print(f"📁 CSV Root: {data_root}")
    print(f"🔗 Neo4j URI: {Config.NEO4J_URI}\n")

    driver = get_driver()

    try:
        # -------- Nodes --------
        protein_csv = data_root / "proteins.csv"
        if protein_csv.exists():
            _safe_load("Proteins", ProteinLoader(driver).load_from_csv, str(protein_csv))
        else:
            print(f"⚠️ Missing: {protein_csv}")

        disease_csv = data_root / "diseases.csv"
        if disease_csv.exists():
            _safe_load("Diseases", DiseaseLoader(driver).load_from_csv, str(disease_csv))
        else:
            print(f"⚠️ Missing: {disease_csv}")

        drug_csv = data_root / "drugs.csv"
        if drug_csv.exists():
            _safe_load("Drugs", DrugLoader(driver).load_from_csv, str(drug_csv))
        else:
            print(f"⚠️ Missing: {drug_csv}")

        trial_csv = data_root / "trials.csv"
        if trial_csv.exists():
            _safe_load("Trials", TrialLoader(driver).load_from_csv, str(trial_csv))
        else:
            print(f"⚠️ Missing: {trial_csv}")

        pub_csv = data_root / "publications.csv"
        if pub_csv.exists():
            _safe_load("Publications", PublicationLoader(driver).load_from_csv, str(pub_csv))
        else:
            print(f"⚠️ Missing: {pub_csv}")

        # -------- Relations --------
        print("\n===============================================")
        print("🔗 Loading Relations")
        print("===============================================")

        rloader = RelationLoader(driver=driver)

        pd_csv = data_root / "protein_disease_relations.csv"
        if pd_csv.exists():
            _safe_load("Protein-Disease relations", rloader.load_protein_disease_from_csv, str(pd_csv))
        else:
            print(f"⚠️ Missing: {pd_csv}")

        dp_csv = data_root / "drug_targets.csv"
        if dp_csv.exists():
            _safe_load("Drug-Protein targets", rloader.load_drug_targets_from_csv, str(dp_csv))
        else:
            print(f"⚠️ Missing: {dp_csv}")

        dd_csv = data_root / "drug_disease_relations.csv"
        if dd_csv.exists():
            _safe_load("Drug-Disease relations", rloader.load_drug_disease_from_csv, str(dd_csv))
        else:
            print(f"⚠️ Missing: {dd_csv}")

        pp_csv = data_root / "protein_similarity.csv"
        if pp_csv.exists():
            _safe_load("Protein-Protein similarity", rloader.load_protein_similarity_from_csv, str(pp_csv))
        else:
            print(f"⚠️ Missing: {pp_csv}")

        td_csv = data_root / "trial_drug_relations.csv"
        if td_csv.exists():
            _safe_load("Trial-Drug relations", rloader.load_trial_drug_from_csv, str(td_csv))
        else:
            print(f"⚠️ Missing: {td_csv}")

        tp_csv = data_root / "trial_protein_relations.csv"
        if tp_csv.exists():
            _safe_load("Trial-Protein relations", rloader.load_trial_protein_from_csv, str(tp_csv))
        else:
            print(f"⚠️ Missing: {tp_csv}")

        pm_csv = data_root / "publication_mentions.csv"
        if pm_csv.exists():
            _safe_load("Publication mentions", rloader.load_publication_mentions_from_csv, str(pm_csv))
        else:
            print(f"⚠️ Missing: {pm_csv}")

    finally:
        close_driver()

    print("\n===============================================")
    print("🎉 GraphDB Build Completed!")
    print("===============================================\n")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ReBio Full Graph Loader")
    parser.add_argument("--data-root", type=str, default=str(Config.RAW_DATA_ROOT))
    args = parser.parse_args()

    build_full_graph(data_root=Path(args.data_root))

import logging
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import pyarrow.dataset as ds

from backend.config import Config

logger = logging.getLogger("open_targets_local")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

RAW = Config.RAW_DATA_ROOT
PROC = Config.PROCESSED_DATA_ROOT

ASSOC_DIR = RAW / "opentargets" / "association_overall_direct"
TARGET_DIR = RAW / "opentargets" / "target"

PROTEINS_CSV = RAW / "proteins.csv"
OUTPUT_CSV = PROC / "disease_associations.csv"


def load_ensembl_to_symbol():
    logger.info("[Load] target/* parquet → EnsemblID→GeneSymbol map")

    ds_targets = ds.dataset(str(TARGET_DIR), format="parquet")
    df = ds_targets.to_table(
        columns=["id", "approvedSymbol"]
    ).to_pandas()

    df.dropna(subset=["approvedSymbol"], inplace=True)
    df["approvedSymbol"] = df["approvedSymbol"].str.upper()

    mapping = dict(zip(df["id"], df["approvedSymbol"]))
    logger.info(f"[Map] Loaded {len(mapping)} gene mappings")

    return mapping


def load_associations():
    logger.info("[Load] association_overall_direct/*.parquet")

    ds_assoc = ds.dataset(str(ASSOC_DIR), format="parquet")
    df = ds_assoc.to_table(
        columns=["targetId", "diseaseId", "score"]
    ).to_pandas()

    logger.info(f"[Load] {len(df)} association rows loaded")
    return df


def run_open_targets_local():
    logger.info("========== Open Targets (Local Parquet) START ==========")

    # 1) proteins.csv → Gene Symbol → UniProt mapping
    df_prot = pd.read_csv(PROTEINS_CSV)
    prot_map = dict(zip(df_prot["gene"].str.upper(), df_prot["uniprot_id"]))

    # 2) Load Ensembl → Gene symbol map
    ens_map = load_ensembl_to_symbol()

    # 3) Load associations
    df_assoc = load_associations()

    # Map targetId → Gene Symbol
    df_assoc["gene"] = df_assoc["targetId"].map(ens_map)

    # Keep only genes we have in ReBio
    df_assoc = df_assoc[df_assoc["gene"].isin(prot_map.keys())]

    # Gene → UniProt ID
    df_assoc["uniprot_id"] = df_assoc["gene"].map(prot_map)
    df_assoc = df_assoc.dropna(subset=["uniprot_id"])

    logger.info(f"[Filter] {len(df_assoc)} matched associations")

    # Build final CSV
    final = df_assoc.rename(columns={"diseaseId": "disease_id"})
    final["source"] = "OpenTargets"
    final["evidence_type"] = "OpenTargets_LocalParquet"
    final["active"] = "true"

    final = final[[
        "uniprot_id",
        "disease_id",
        "score",
        "source",
        "evidence_type",
        "active"
    ]]

    PROC.mkdir(parents=True, exist_ok=True)
    final.to_csv(OUTPUT_CSV, index=False)
    logger.info(f"[Success] Saved → {OUTPUT_CSV}")

    logger.info("========== Open Targets (Local Parquet) DONE ===========")


if __name__ == "__main__":
    run_open_targets_local()

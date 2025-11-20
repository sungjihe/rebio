# backend/pipeline/pdb_downloader.py
import requests
from pathlib import Path
from typing import List
from tqdm import tqdm

from backend.config import Config

# -----------------------------
# ⭐ 반드시 모듈 최상단에서 선언해야 NameError가 해결됨
# -----------------------------
RAW_DATA_ROOT = Config.RAW_DATA_ROOT
PDB_ROOT = Config.PDB_ROOT

RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_DOWNLOAD = "https://files.rcsb.org/download/{}.pdb"
ALPHAFOLD_DOWNLOAD = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb"


def get_pdb_ids_from_uniprot(uniprot_id: str) -> List[str]:
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {
                "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                "operator": "exact_match",
                "value": uniprot_id
            }
        },
        "request_options": {"return_all_hits": True},
        "return_type": "entry"
    }

    res = requests.post(RCSB_SEARCH, json=query, timeout=10)
    if res.status_code != 200:
        return []

    data = res.json()
    return [item["identifier"] for item in data.get("result_set", [])]


def download_pdb(pdb_id: str, dest: Path) -> bool:
    url = RCSB_DOWNLOAD.format(pdb_id)
    res = requests.get(url, timeout=10)

    if res.status_code == 200 and b"HEADER" in res.content[:200]:
        dest.write_bytes(res.content)
        return True
    return False


def download_alphafold(uniprot_id: str, dest: Path) -> bool:
    url = ALPHAFOLD_DOWNLOAD.format(uniprot_id)
    res = requests.get(url, timeout=10)

    if res.status_code == 200 and b"ATOM" in res.content[:200]:
        dest.write_bytes(res.content)
        return True
    return False


def download_all_pdbs():
    proteins_csv = RAW_DATA_ROOT / "proteins.csv"
    if not proteins_csv.exists():
        raise FileNotFoundError(f"{proteins_csv} not found")

    # Read UniProt IDs
    uniprot_ids = []
    with open(proteins_csv, "r") as f:
        next(f)
        for line in f:
            uniprot_ids.append(line.split(",")[0].strip())

    PDB_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"[PDB] Downloading structures for {len(uniprot_ids)} proteins")

    for uid in tqdm(uniprot_ids):
        out = PDB_ROOT / f"{uid}.pdb"
        if out.exists():
            continue

        pdb_ids = get_pdb_ids_from_uniprot(uid)

        success = False
        for pdb_id in pdb_ids:
            if download_pdb(pdb_id, out):
                success = True
                break

        if not success:
            download_alphafold(uid, out)

    print("[PDB] Completed.")

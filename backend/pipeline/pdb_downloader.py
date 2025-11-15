# backend/pipeline/pdb_downloader.py
import os
import requests
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm

from .config import PDB_ROOT, RAW_DATA_ROOT


RCSB_SEARCH = "https://search.rcsb.org/rcsbsearch/v2/query"
RCSB_DOWNLOAD = "https://files.rcsb.org/download/{}.pdb"
ALPHAFOLD_DOWNLOAD = "https://alphafold.ebi.ac.uk/files/AF-{}-F1-model_v4.pdb"


def get_pdb_ids_from_uniprot(uniprot_id: str) -> List[str]:
    """RCSB 검색 API를 사용하여 UniProt → PDB 구조 ID 얻기."""
    query = {
        "query": {
            "type": "terminal",
            "service": "text",
            "parameters": {"attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession", "operator": "exact_match", "value": uniprot_id}
        },
        "request_options": {"return_all_hits": True},
        "return_type": "entry"
    }

    res = requests.post(RCSB_SEARCH, json=query, timeout=10)
    if res.status_code != 200:
        return []

    data = res.json()
    ids = [item["identifier"] for item in data.get("result_set", [])]
    return ids


def download_pdb(pdb_id: str, dest: Path) -> bool:
    """단일 PDB 구조 다운로드."""
    url = RCSB_DOWNLOAD.format(pdb_id)
    res = requests.get(url, timeout=10)

    if res.status_code == 200 and b"HEADER" in res.content[:200]:
        dest.write_bytes(res.content)
        return True
    return False


def download_alphafold(uniprot_id: str, dest: Path) -> bool:
    """UniProt 기반 AlphaFold 구조 다운로드."""
    url = ALPHAFOLD_DOWNLOAD.format(uniprot_id)
    res = requests.get(url, timeout=10)

    if res.status_code == 200 and b"ATOM" in res.content[:200]:
        dest.write_bytes(res.content)
        return True
    return False


def download_all_pdbs():
    """raw/proteins.csv에서 uniprot_id 목록을 읽고 구조 파일 자동 다운로드."""
    proteins_csv = RAW_DATA_ROOT / "proteins.csv"
    if not proteins_csv.exists():
        raise FileNotFoundError(f"{proteins_csv} not found")

    uniprot_ids = []
    with open(proteins_csv, "r") as f:
        next(f)
        for line in f:
            uniprot_id = line.split(",")[0].strip()
            uniprot_ids.append(uniprot_id)

    PDB_ROOT.mkdir(parents=True, exist_ok=True)

    print(f"[PDB] Downloading structures for {len(uniprot_ids)} proteins")

    for uid in tqdm(uniprot_ids):
        out_path = PDB_ROOT / f"{uid}.pdb"
        if out_path.exists():
            continue

        pdb_ids = get_pdb_ids_from_uniprot(uid)

        success = False
        for pdb_id in pdb_ids:
            if download_pdb(pdb_id, out_path):
                success = True
                break

        if not success:
            # fallback → AlphaFold
            download_alphafold(uid, out_path)

    print(f"[PDB] Completed.")

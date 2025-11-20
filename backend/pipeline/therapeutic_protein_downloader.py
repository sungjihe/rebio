# backend/pipeline/therapeutic_protein_downloader.py

import csv
import requests
from backend.config import Config
RAW_DATA_ROOT = Config.RAW_DATA_ROOT

UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb/search"


def fetch_therapeutic_protein(name: str):
    """
    치료용 단백질/항체 약물은 UniProt에서 sequence 기반으로 수집한다.
    """
    params = {
        "query": f"({name}) AND reviewed:true",
        "format": "tsv",
        "fields": "accession,protein_name,gene_primary,sequence",
        "size": 1,
    }

    r = requests.get(UNIPROT_BASE, params=params, timeout=20)
    if r.status_code != 200:
        return None

    lines = r.text.splitlines()
    if len(lines) < 2:
        return None

    parts = lines[1].split("\t")
    if len(parts) < 4:
        return None

    accession, protein_name, gene, seq = parts[:4]

    return {
        "drug_name": name,
        "uniprot_id": accession,
        "sequence": seq,
        "protein_name": protein_name or name,
        "gene": gene or None
    }


def download_therapeutic_proteins(names):
    out_path = RAW_DATA_ROOT / "therapeutic_proteins.csv"

    rows = []
    for name in names:
        print(f"[Therapeutic] Fetching {name}")
        rec = fetch_therapeutic_protein(name)
        if rec:
            rows.append(rec)

    if not rows:
        print("⚠ No therapeutic proteins fetched.")
        return

    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["drug_name", "uniprot_id", "protein_name", "gene", "sequence"],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Saved therapeutic proteins → {out_path}")

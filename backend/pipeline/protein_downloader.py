import os
import requests
import pandas as pd
from typing import List
from .config import RAW_DATA

UNIPROT_API = "https://rest.uniprot.org/uniprotkb/"

def fetch_protein(uniprot_id: str):
    url = UNIPROT_API + uniprot_id + ".json"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    js = r.json()

    sequence = js.get("sequence", {}).get("value", "")
    gene = js.get("genes", [{}])[0].get("geneName", {}).get("value", "")
    name = js.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value", "")

    pdb_ids = []
    for db in js.get("dbReferences", []):
        if db.get("type") == "PDB":
            pdb_ids.append(db.get("id"))

    return {
        "uniprot_id": uniprot_id,
        "name": name,
        "gene": gene,
        "sequence": sequence,
        "pdb_ids": ";".join(pdb_ids),
        "embedding_id": uniprot_id + "_vec"
    }

def download_proteins(uniprot_ids: List[str]):
    rows = []
    for uid in uniprot_ids:
        d = fetch_protein(uid)
        if d:
            rows.append(d)

    df = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA, "proteins.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved proteins → {out_path}")

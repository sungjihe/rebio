import os
import requests
import pandas as pd
from .config import RAW_DATA_ROOT


PUBCHEM_API = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"

def fetch_pubchem(name: str):
    url = PUBCHEM_API + name + "/property/IsomericSMILES,CanonicalSMILES/JSON"
    r = requests.get(url)
    if r.status_code != 200:
        return None
    js = r.json()
    props = js["PropertyTable"]["Properties"][0]
    return {
        "name": name,
        "smiles": props.get("IsomericSMILES"),
        "pubchem_cid": props.get("CID"),
        "drugbank_id": f"DB_{name.upper()}"
    }

def download_drugs(drug_list):
    rows = []
    for name in drug_list:
        d = fetch_pubchem(name)
        if d:
            rows.append(d)

    df = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA_ROOT, "drugs.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved drugs → {out_path}")

import os
import pandas as pd
import requests
from .config import RAW_DATA_ROOT


MONDO_SEARCH_API = "https://www.ebi.ac.uk/ols4/api/search?q="

def fetch_disease(name: str):
    url = MONDO_SEARCH_API + name
    r = requests.get(url)
    js = r.json()

    items = js.get("response", {}).get("docs", [])
    if not items:
        return None

    best = items[0]
    return {
        "disease_id": best.get("obo_id", ""),
        "name": best.get("label", name)
    }

def download_diseases(name_list):
    rows = []
    for name in name_list:
        d = fetch_disease(name)
        if d:
            rows.append(d)

    df = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA_ROOT, "diseases.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved diseases → {out_path}")

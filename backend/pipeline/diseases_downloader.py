import os
import pandas as pd
import requests

from backend.config import Config

RAW_DATA_ROOT = Config.RAW_DATA_ROOT

MONDO_SEARCH_API = "https://www.ebi.ac.uk/ols4/api/search?q="


def fetch_disease(name: str):
    """
    MONDO disease exact search helper.
    """
    url = MONDO_SEARCH_API + name
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
    except Exception as e:
        print(f"[MONDO] Error fetching {name} → {e}")
        return None

    js = r.json()
    items = js.get("response", {}).get("docs", [])

    if not items:
        print(f"[MONDO] No hit for {name}")
        return None

    best = items[0]
    return {
        "disease_id": best.get("obo_id", ""),
        "name": best.get("label", name),
    }


def download_diseases(name_list):
    """
    Download MONDO diseases for a list of names.
    Output → data/raw/diseases.csv
    """
    rows = []

    for name in name_list:
        print(f"[MONDO] Fetching disease: {name}")
        d = fetch_disease(name)
        if d:
            rows.append(d)

    if not rows:
        print("[MONDO] No diseases found.")
        return

    df = pd.DataFrame(rows)
    out_path = RAW_DATA_ROOT / "diseases.csv"
    df.to_csv(out_path, index=False, encoding="utf-8")

    print(f"[OK] Saved diseases → {out_path}")

import os
import requests
import pandas as pd
import time
from .config import RAW_DATA

# NEW API
API = "https://clinicaltrials.gov/api/query/study_fields"


def fetch_trial(drug):
    params = {
        "expr": drug,
        "fields": "NCTId,OverallStatus,WhyStopped,Phase,StartDate",
        "max_rnk": 100,
        "fmt": "JSON"
    }

    try:
        r = requests.get(API, params=params, timeout=10)
    except Exception as e:
        print(f"[ERROR] Request failed for {drug}: {e}")
        return []

    # JSON 파싱 시도
    try:
        data = r.json()
    except ValueError:
        print(f"[WARN] NON-JSON response for '{drug}' — skipping.")
        print(r.text[:200])
        return []

    studies = (
        data.get("StudyFieldsResponse", {})
            .get("StudyFields", [])
    )

    if not studies:
        print(f"[WARN] No studies found for: {drug}")
        return []

    rows = []

    for s in studies:
        rows.append({
            "nct_id": s.get("NCTId", [""])[0],
            "status": s.get("OverallStatus", [""])[0],
            "whyStopped": s.get("WhyStopped", [""])[0],
            "phase": s.get("Phase", [""])[0],
            "start_date": s.get("StartDate", [""])[0],
        })

    time.sleep(0.3)   # API 제한 방지
    return rows


def download_trials(drug_list):
    rows = []

    for drug in drug_list:
        print(f"[INFO] Fetching trials for: {drug}")
        rows.extend(fetch_trial(drug))

    if not rows:
        print("[WARN] No trial data collected.")

    df = pd.DataFrame(rows)
    out_path = os.path.join(RAW_DATA, "trials.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved trials → {out_path}")

# backend/pipeline/trial_downloader.py

import requests
import logging
import csv
import os

logger = logging.getLogger("trials")

API_URL = "https://clinicaltrials.gov/api/v2/studies"


def fetch_trials_v2(therapeutic_name: str):
    """
    ClinicalTrials.gov v2 API
    치료용 단백질 / 항체 / fusion protein / cytokine 이름 기반으로 trial 검색
    """
    params = {
        "query.term": therapeutic_name,
        "pageSize": 100
    }

    try:
        r = requests.get(API_URL, params=params, timeout=20)
    except Exception as e:
        logger.error(f"HTTP error for {therapeutic_name}: {e}")
        return []

    if r.status_code != 200:
        logger.error(f"HTTP {r.status_code} for {therapeutic_name}")
        return []

    data = r.json()
    studies = data.get("studies", [])

    results = []
    for s in studies:
        try:
            ident = s["protocolSection"]["identificationModule"]
            status_mod = s["protocolSection"]["statusModule"]
            design_mod = s["protocolSection"]["designModule"]

            nct = ident.get("nctId", "")
            status = status_mod.get("overallStatus", "")
            start = status_mod.get("startDateStruct", {}).get("startDate", "")
            why_stopped = status_mod.get("whyStopped", "")
            phase = design_mod.get("phases", [])

            phase_str = ",".join(phase) if isinstance(phase, list) else phase

            results.append([
                nct,
                therapeutic_name,   # drug_name → therapeutic_name
                status,
                phase_str,
                start,
                why_stopped
            ])
        except Exception as e:
            logger.warning(f"Error parsing study: {e}")

    return results


def download_trials(therapeutic_names, out_path="./data/raw/trials.csv"):
    rows = []

    for name in therapeutic_names:
        logger.info(f"[Trials] Fetching trials for: {name}")
        rows.extend(fetch_trials_v2(name))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["nct_id", "therapeutic_name", "status", "phase", "start_date", "why_stopped"]
        )
        writer.writerows(rows)

    logger.info(f"[OK] Saved trials → {out_path}")


import requests
import logging
import csv
import os

logger = logging.getLogger("trials")

API_URL = "https://clinicaltrials.gov/api/v2/studies"

FIELDS = [
    "protocolSection.identificationModule.nctId",
    "protocolSection.statusModule.overallStatus",
    "protocolSection.statusModule.startDateStruct.startDate",
    "protocolSection.designModule.phases",
    "protocolSection.statusModule.whyStopped"
]


def fetch_trials_v2(drug_name):
    params = {
        "query.term": drug_name,
        "pageSize": 100
    }

    r = requests.get(API_URL, params=params, timeout=20)

    if r.status_code != 200:
        logger.warn(f"HTTP {r.status_code} for {drug_name}")
        return []

    data = r.json()
    if "studies" not in data:
        logger.warn(f"No 'studies' field for {drug_name}")
        return []

    results = []

    for s in data["studies"]:
        try:
            nct = s["protocolSection"]["identificationModule"]["nctId"]
            phase = s["protocolSection"]["designModule"].get("phases", [])
            status = s["protocolSection"]["statusModule"].get("overallStatus", "")
            start = s["protocolSection"]["statusModule"].get("startDateStruct", {}).get("startDate", "")
            why_stopped = s["protocolSection"]["statusModule"].get("whyStopped", "")

            phase_str = ",".join(phase) if isinstance(phase, list) else phase

            results.append([
                nct,
                drug_name,
                status,
                phase_str,
                start,
                why_stopped
            ])
        except Exception as e:
            logger.error(f"Error parsing study: {e}")

    return results


def download_trials(drugs_list, out_path="./data/raw/trials.csv"):
    rows = []
    for drug in drugs_list:
        logger.info(f"[Trials] Fetching: {drug}")
        rows.extend(fetch_trials_v2(drug))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)

    with open(out_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["nct_id", "drug_name", "status", "phase", "start_date", "why_stopped"])
        writer.writerows(rows)

    logger.info(f"[OK] Saved trials → {out_path}")

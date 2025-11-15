# backend/crawlers/nct_crawler.py
import requests


def fetch_clinical_trials(query: str, max_results: int = 5):
    """
    ClinicalTrials.gov API 검색
    """
    url = (
        "https://clinicaltrials.gov/api/query/study_fields"
        f"?expr={query.replace(' ', '+')}"
        "&fields=NCTId,Condition,BriefTitle,Phase,Status"
        f"&min_rnk=1&max_rnk={max_results}&fmt=json"
    )

    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return None

    studies = res.json().get("StudyFieldsResponse", {}).get("StudyFields", [])
    return studies

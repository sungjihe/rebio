# backend/crawlers/nct_crawler.py

from backend.crawlers.common import safe_get

def fetch_clinical_trials(query: str, max_results: int = 5):
    expr = query.replace(" ", "+")
    url = (
        "https://clinicaltrials.gov/api/query/study_fields"
        f"?expr={expr}&fields=NCTId,Condition,BriefTitle,Phase,Status"
        f"&min_rnk=1&max_rnk={max_results}&fmt=json"
    )

    res = safe_get(url)

    if not res:
        return {
            "ok": False,
            "source": "clinicaltrials",
            "data": None,
            "error": "request_failed"
        }

    studies = res.json().get("StudyFieldsResponse", {}).get("StudyFields", [])

    return {
        "ok": True,
        "source": "clinicaltrials",
        "data": studies,
        "error": None,
    }

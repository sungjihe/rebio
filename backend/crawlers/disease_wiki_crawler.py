# backend/crawlers/disease_wiki_crawler.py

from bs4 import BeautifulSoup
from backend.crawlers.common import safe_get

def fetch_wiki_summary(disease_name: str):
    url = f"https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}"
    res = safe_get(url)

    if not res:
        return {
            "ok": False,
            "source": "wikipedia",
            "data": None,
            "error": "request_failed"
        }

    soup = BeautifulSoup(res.text, "html.parser")
    paragraphs = soup.select("p")

    text = " ".join(p.text.strip() for p in paragraphs[:3])

    return {
        "ok": True,
        "source": "wikipedia",
        "data": text or None,
        "error": None,
    }



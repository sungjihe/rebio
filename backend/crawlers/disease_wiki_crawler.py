# backend/crawlers/disease_wiki_crawler.py
import requests
from bs4 import BeautifulSoup


def fetch_wiki_summary(disease_name: str):
    """Wikipedia 질병 요약"""
    url = f"https://en.wikipedia.org/wiki/{disease_name.replace(' ', '_')}"
    res = requests.get(url, timeout=10)

    if res.status_code != 200:
        return None

    soup = BeautifulSoup(res.text, "html.parser")

    paragraphs = soup.select("p")
    text = " ".join(p.text.strip() for p in paragraphs[:3])

    return text if text else None


# backend/crawlers/pubmed_crawler.py

import logging
import requests
import xml.etree.ElementTree as ET

logger = logging.getLogger("PubMedCrawler")
logging.basicConfig(level=logging.INFO)

PUBMED_SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def search_pubmed_summaries(query: str, max_results: int = 5):
    """
    PubMed에서 검색어 기반으로 PMID 리스트 가져오기 → 요약 텍스트 추출
    """

    try:
        # 1) PMID 검색
        res = requests.get(
            PUBMED_SEARCH_URL,
            params={
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
            },
            timeout=10
        )
        res.raise_for_status()
        root = ET.fromstring(res.text)

        pmids = [id_elem.text for id_elem in root.findall(".//Id")]

        if not pmids:
            return {
                "ok": True,
                "source": "pubmed",
                "data": [],
                "error": None,
            }

        # 2) PMID로 상세 요약 가져오기
        fetch_res = requests.get(
            PUBMED_FETCH_URL,
            params={
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml"
            },
            timeout=10
        )
        fetch_res.raise_for_status()

        fetch_root = ET.fromstring(fetch_res.text)
        articles = []

        for article in fetch_root.findall(".//PubmedArticle"):
            summary_nodes = article.findall(".//AbstractText")
            summary = " ".join(node.text or "" for node in summary_nodes)

            title_node = article.find(".//ArticleTitle")
            title = title_node.text if title_node is not None else None

            pmid_node = article.find(".//PMID")
            pmid = pmid_node.text if pmid_node is not None else None

            articles.append({
                "pmid": pmid,
                "title": title,
                "summary": summary
            })

        return {
            "ok": True,
            "source": "pubmed",
            "data": articles,
            "error": None,
        }

    except Exception as e:
        logger.error(f"[PubMedCrawler] Error: {e}")
        return {
            "ok": False,
            "source": "pubmed",
            "data": None,
            "error": str(e),
        }

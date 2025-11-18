# backend/agentic/nodes/crawler_node.py

import logging
from typing import Dict, Any, Optional

from backend.agentic.state import HeliconState

# 외부 크롤러
from backend.crawlers.disease_wiki_crawler import fetch_wikipedia_summary
from backend.crawlers.pubchem_crawler import fetch_pubchem_info
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary
from backend.crawlers.pubmed_crawler import search_pubmed_summaries

logger = logging.getLogger("CrawlerNode")
logging.basicConfig(level=logging.INFO)


class CrawlerNode:
    """
    외부 생물학 데이터 소스에서 추가 근거를 불러오는 Multi-Agent 노드.
    Wikipedia / PubChem / UniProt / PubMed 등 지원.
    """

    SKIP_INTENTS = {
        "protein_redesign",
        "structure_prediction",
        "structure_render",
    }

    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        question = state.question or ""

        if intent in self.SKIP_INTENTS:
            logger.info(f"[CrawlerNode] Skipping crawling because intent={intent}")
            state.enriched_data = {}
            state.log("crawler_node", {"skipped": True})
            return state

        enriched: Dict[str, Any] = {
            "wiki": None,
            "pubchem": None,
            "uniprot": None,
            "pubmed": None,
        }

        # ─────────────────────────────────────────────
        # Wikipedia
        # ─────────────────────────────────────────────
        try:
            enriched["wiki"] = fetch_wikipedia_summary(question)
        except Exception as e:
            logger.warning(f"[CrawlerNode] Wikipedia error: {e}")

        # ─────────────────────────────────────────────
        # PubChem
        # ─────────────────────────────────────────────
        try:
            enriched["pubchem"] = fetch_pubchem_info(question)
        except Exception as e:
            logger.warning(f"[CrawlerNode] PubChem error: {e}")

        # ─────────────────────────────────────────────
        # UniProt (단백질 이름 패턴이 포함된 경우만)
        # ─────────────────────────────────────────────
        try:
            enriched["uniprot"] = fetch_uniprot_summary(question)
        except Exception as e:
            logger.warning(f"[CrawlerNode] UniProt error: {e}")

        # ─────────────────────────────────────────────
        # PubMed (키워드 기반)
        # ─────────────────────────────────────────────
        try:
            enriched["pubmed"] = search_pubmed_summaries(question, max_results=5)
        except Exception as e:
            logger.warning(f"[CrawlerNode] PubMed error: {e}")

        # 상태 저장
        state.enriched_data = enriched

        # 로깅 저장
        state.log("crawler_node", {
            "wiki_found": enriched["wiki"] is not None,
            "pubchem_found": enriched["pubchem"] is not None,
            "uniprot_found": enriched["uniprot"] is not None,
            "pubmed_results": len(enriched["pubmed"] or []),
        })

        logger.info("[CrawlerNode] Finished crawling step.")
        return state

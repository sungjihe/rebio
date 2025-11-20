# backend/agentic/nodes/crawler_node.py

import logging
from backend.agentic.state import HeliconState

# --- Crawlers ---
from backend.crawlers.disease_wiki_crawler import fetch_wiki_summary
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary
from backend.crawlers.nct_crawler import fetch_clinical_trials

# PubMed crawler (파일명은 pubmed_crawler.py 라고 가정)
from backend.crawlers.pubmed_crawler import search_pubmed_summaries

logger = logging.getLogger("CrawlerNode")
logging.basicConfig(level=logging.INFO)


class CrawlerNode:
    """
    Crawls Wikipedia, UniProt, PubMed, ClinicalTrials.gov
    """

    SKIP_INTENTS = {
        "protein_design",
        "structure_prediction",
        "structure_render",
    }

    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        question = state.question or ""

        # 특정 intent 에서는 크롤러 생략
        if intent in self.SKIP_INTENTS:
            state.enriched_data = {}
            return state

        logger.info("[CrawlerNode] Running crawlers...")

        enriched = {
            "wiki": None,
            "uniprot": None,
            "pubmed": None,
            "clinical_trials": None,
        }

        # Wikipedia
        try:
            enriched["wiki"] = fetch_wiki_summary(question)
        except Exception as e:
            logger.warning(f"[CrawlerNode] Wikipedia error: {e}")

        # UniProt
        try:
            enriched["uniprot"] = fetch_uniprot_summary(question)
        except Exception as e:
            logger.warning(f"[CrawlerNode] UniProt error: {e}")

        # PubMed
        try:
            enriched["pubmed"] = search_pubmed_summaries(question, max_results=5)
        except Exception as e:
            logger.warning(f"[CrawlerNode] PubMed error: {e}")

        # ClinicalTrials.gov
        try:
            enriched["clinical_trials"] = fetch_clinical_trials(question, max_results=5)
        except Exception as e:
            logger.warning(f"[CrawlerNode] ClinicalTrials error: {e}")

        state.enriched_data = enriched
        return state

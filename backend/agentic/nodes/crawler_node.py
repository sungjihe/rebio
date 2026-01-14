# backend/agentic/nodes/crawler_node.py

import logging
from backend.agentic.state import HeliconState

from backend.crawlers.disease_wiki_crawler import fetch_wiki_summary
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary
from backend.crawlers.nct_crawler import fetch_clinical_trials
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
        entities = state.entities or {}   # ✅ None-safe

        # 특정 intent에서는 크롤러 생략
        if intent in self.SKIP_INTENTS:
            state.enriched_data = {}
            state.log("crawler_node", {"skipped": True, "intent": intent})
            return state

        logger.info("[CrawlerNode] Running crawlers...")

        enriched = {
            "wiki": None,
            "uniprot": None,
            "pubmed": None,
            "clinical_trials": None,
        }

        # --- Inputs (없으면 스킵) ---
        disease_name = entities.get("disease_name") or entities.get("disease")  # 유연하게
        uniprot_id = entities.get("uniprot_id")
        therapeutic_name = entities.get("therapeutic_name") or entities.get("drug_name")

        # Wikipedia
        if disease_name:
            try:
                enriched["wiki"] = fetch_wiki_summary(disease_name)
            except Exception as e:
                logger.warning(f"[CrawlerNode] Wikipedia error: {e}")

        # UniProt
        if uniprot_id:
            try:
                enriched["uniprot"] = fetch_uniprot_summary(uniprot_id)
            except Exception as e:
                logger.warning(f"[CrawlerNode] UniProt error: {e}")

        # PubMed (질문 텍스트 기반은 항상 가능)
        try:
            enriched["pubmed"] = search_pubmed_summaries(question, max_results=5)
        except Exception as e:
            logger.warning(f"[CrawlerNode] PubMed error: {e}")

        # ClinicalTrials.gov (치료제/항체 이름이 있을 때만)
        if therapeutic_name:
            try:
                enriched["clinical_trials"] = fetch_clinical_trials(therapeutic_name, max_results=5)
            except Exception as e:
                logger.warning(f"[CrawlerNode] ClinicalTrials error: {e}")

        state.enriched_data = enriched
        state.log("crawler_node", {"success": True, "has": {k: (v is not None) for k, v in enriched.items()}})
        return state

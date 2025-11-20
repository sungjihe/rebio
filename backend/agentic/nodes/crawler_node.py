class CrawlerNode:

    SKIP_INTENTS = {
        "protein_design",
        "structure_prediction",
        "structure_render",
    }

    def run(self, state: HeliconState) -> HeliconState:
        intent = state.intent
        question = state.question or ""

        if intent in self.SKIP_INTENTS:
            state.enriched_data = {}
            return state

        enriched = {
            "wiki": None,
            "uniprot": None,
            "pubmed": None,
        }

        # Wikipedia
        try:
            enriched["wiki"] = fetch_wikipedia_summary(question)
        except:
            pass

        # UniProt
        try:
            enriched["uniprot"] = fetch_uniprot_summary(question)
        except:
            pass

        # PubMed
        try:
            enriched["pubmed"] = search_pubmed_summaries(question, max_results=5)
        except:
            pass

        state.enriched_data = enriched
        return state


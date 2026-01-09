# backend/agentic/nodes/supervisor_node.py

 import logging
 from backend.agentic.state import HeliconState
 
 logger = logging.getLogger("Supervisor")
 logging.basicConfig(level=logging.INFO)
 
 class SupervisorNode:
     """
     Dynamic Router for Helicon Multi-Agent Workflow.
     """
     # If a node is repeatedly selected without progress, break to HITL.
     MAX_ATTEMPTS = 2 

     def run(self, state: HeliconState) -> HeliconState:
         next_step = self.decide_next(state)
         state.next_node = next_step
         state.log("supervisor", {"next_node": next_step})
         return state
 
     # -----------------------------------------------------
     def decide_next(self, state: HeliconState):
 
         # 1) Intent first
         if state.intent is None:
             return "intent"
 
         # 2) Entity extraction
         if not state.entities:
             return "entity"
 
         # 3) Vision check

        need_vision = False
        image_path = state.entities.get("image_path") if isinstance(state.entities, dict) else None

        if image_path and state.vision_data is None:
            need_vision = True
 
         vision_keywords = ["image", "figure", "plot", "chart", "gel", "microscopy"]
        q = (state.question or "").lower()
        if any(k in q for k in vision_keywords):
             if state.vision_data is None:
                 need_vision = True
 
         if need_vision:
             return "vision"
 
        # 4) Graph search (with loop-guard + HITL)
        if state.graph_result is None:
            # If graph is required but missing uniprot_id, graph will never progress.
            entities = state.entities or {}
            uniprot_id = entities.get("uniprot_id") if isinstance(entities, dict) else None

            # Count attempts
            n = state.bump_attempt("graph")

            # If we already know we cannot proceed, trigger HITL early.
            if not uniprot_id:
                if n >= self.MAX_ATTEMPTS:
                    return self._to_human_missing_uniprot(state)
                # Try entity extraction again once, in case upstream LLM missed it.
                # (Still minimal; does not add new nodes.)
                return "entity"

            # We have uniprot_id, attempt graph normally.
            if n >= self.MAX_ATTEMPTS:
                # Even with uniprot_id, repeated None suggests GraphSearchClient failure or data gap.
                return self._to_human_graph_failed(state)
            return "graph"
        else:
            # Progress made -> reset attempt counter
            state.reset_attempt("graph")


        # 5) Evidence (with loop-guard + HITL)
        if state.evidence_paths is None:
            intent = state.intent or ""
            entities = state.entities or {}
            uniprot_id = entities.get("uniprot_id") if isinstance(entities, dict) else None
            graph = state.graph_result

            n = state.bump_attempt("evidence")

            # If no uniprot, evidence will never progress.
            if not uniprot_id:
                if n >= self.MAX_ATTEMPTS:
                    return self._to_human_missing_uniprot(state, node="evidence")
                return "entity"

            # For intents that do not rely on evidence, we can safely "skip" evidence.
            # This also prevents pointless loops on general_search.
            if intent not in ("disease_prediction", "therapeutic_recommendation", "evidence_paths"):
                # Mark evidence as done (empty) to avoid looping.
                state.evidence_paths = []
                state.reset_attempt("evidence")
                return self.decide_next(state)

            # If graph is empty or None-like, evidence can't select target_id.
            # EvidenceNode currently chooses target_id from graph[0], so it will fail if graph is [].
           if not graph:
                if n >= self.MAX_ATTEMPTS:
                    return self._to_human_missing_target(state)
                # Re-run graph once in case it was transient.
                return "graph"

            # We have prerequisites; attempt evidence normally.
            if n >= self.MAX_ATTEMPTS:
                return self._to_human_evidence_failed(state)
            return "evidence"
        else:
            state.reset_attempt("evidence")
 
 
         # 6) Web crawling
       
        # canonical: enriched_data
         if state.enriched_data is None:
             return "crawler"
 
         # 7) Protein design
       
        # canonical: designed_protein
        if state.intent == "protein_design" and state.designed_protein is None:
             return "design"
 
         # 8) Structure prediction
        
        # structure is relevant when we have designed variants OR an input sequence
        has_seq = bool((state.entities or {}).get("protein_sequence"))
        has_design = bool(state.designed_protein)
        if (has_design or has_seq) and state.intent == "protein_design" and state.structure_result is None:
             return "structure"
 
         # 9) Render 3D
         if state.structure_result and state.structure_image is None:
             return "render"
 
         # 10) Reasoning aggregation
         if state.reasoning_summary is None:
             return "reason"
 
         # 11) Final
         return "final"

    # =====================================================
    # HITL payload builders
    # =====================================================
    def _to_human_missing_uniprot(self, state: HeliconState, node: str = "graph") -> str:
        state.halt_reason = "missing_uniprot_id"
        state.human_request = {
            "node": node,
            "reason": "missing_uniprot_id",
            "message": "Graph/Evidence analysis requires a UniProt ID. Provide uniprot_id or choose to skip graph-based steps.",
            "required_fields": ["entities.uniprot_id"],
            "actions": [
                {"type": "input", "field": "entities.uniprot_id", "label": "UniProt ID (e.g., P12345)"},
                {"type": "button", "value": "skip_graph", "label": "Skip graph/evidence and continue with crawler-based answer"},
                {"type": "button", "value": "stop", "label": "Stop"},
            ],
        }
        return "human"

    def _to_human_missing_target(self, state: HeliconState) -> str:
        state.halt_reason = "missing_target_id"
        state.human_request = {
            "node": "evidence",
            "reason": "missing_target_id",
            "message": "Evidence paths require a target (disease or therapeutic protein). Graph results are empty. Choose how to proceed.",
            "required_fields": [],
            "actions": [
                {"type": "button", "value": "skip_evidence", "label": "Skip evidence paths and continue"},
                {"type": "button", "value": "retry_graph", "label": "Retry graph search"},
                {"type": "button", "value": "stop", "label": "Stop"},
            ],
        }
        return "human"

    def _to_human_graph_failed(self, state: HeliconState) -> str:
        state.halt_reason = "graph_no_progress"
        state.human_request = {
            "node": "graph",
            "reason": "graph_no_progress",
            "message": "Graph search did not produce results after multiple attempts. Choose to retry, skip, or stop.",
            "required_fields": [],
            "actions": [
                {"type": "button", "value": "retry_graph", "label": "Retry graph search"},
                {"type": "button", "value": "skip_graph", "label": "Skip graph/evidence and continue"},
                {"type": "button", "value": "stop", "label": "Stop"},
            ],
        }
        return "human"

    def _to_human_evidence_failed(self, state: HeliconState) -> str:
        state.halt_reason = "evidence_no_progress"
        state.human_request = {
            "node": "evidence",
            "reason": "evidence_no_progress",
            "message": "Evidence path search did not produce results after multiple attempts. Choose to retry, skip, or stop.",
            "required_fields": [],
            "actions": [
                {"type": "button", "value": "retry_evidence", "label": "Retry evidence search"},
                {"type": "button", "value": "skip_evidence", "label": "Skip evidence paths and continue"},
                {"type": "button", "value": "stop", "label": "Stop"},
            ],
        }
        return "human"

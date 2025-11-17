import os
import json
import logging
from typing import Dict, Any, Optional, List

import requests

from backend.graph.graph_search_client import GraphSearchClient
from backend.crawlers.disease_wiki_crawler import fetch_wikipedia_summary
from backend.crawlers.pubchem_crawler import fetch_pubchem_info
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary

from backend.agent.protein_redesign_node import ProteinRedesignNode, ProteinRedesignInput
from backend.agent.graph_evidence_path_node import GraphEvidencePathNode
from backend.agent.relation_weighting_node import RelationWeightingNode

logger = logging.getLogger("GraphWorkflow")
logging.basicConfig(level=logging.INFO)

# Node instances
protein_redesign_node = ProteinRedesignNode()
evidence_node = GraphEvidencePathNode()
relation_weighting = RelationWeightingNode()


# ====================================================
# LLM Helper (Ollama + BioMistral)
# ====================================================
def _llm(prompt: str) -> str:
    payload = {
        "model": "biomistral",
        "prompt": prompt,
        "stream": False,
    }
    try:
        res = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        res.raise_for_status()
        return res.json().get("response", "").strip()
    except Exception as e:
        logger.error(f"[LLM] Error calling BioMistral: {e}")
        return f"[LLM Error] {e}"


# ====================================================
# Node 1 — Intent Classification
# ====================================================
def node_intent(question: str) -> Dict[str, Any]:
    prompt = f"""
아래 사용자의 질문을 보고 Intent를 하나만 선택하세요.

[가능한 Intent]
protein_similarity
disease_prediction
drug_recommendation
evidence_paths
protein_redesign
general_search

질문:
{question}

위 목록 중 하나만 출력하세요.
"""
    intent = _llm(prompt).strip()
    return {"intent": intent}


# ====================================================
# Node 2 — Entity Extraction
# ====================================================
def node_extract_entities(question: str) -> Dict[str, Any]:
    prompt = f"""
아래 질문에서 엔터티를 JSON으로 추출하세요.

반환 JSON 키:
- uniprot_id
- disease_id
- drugbank_id
- protein_sequence

질문:
{question}

반드시 다음 형식의 JSON만 출력:
{{
  "uniprot_id": null,
  "disease_id": null,
  "drugbank_id": null,
  "protein_sequence": null
}}
"""
    try:
        raw = _llm(prompt)
        entities = json.loads(raw)
    except Exception as e:
        logger.error(f"[Entity Extraction] JSON parsing error: {e}")
        entities = {}

    for k in ["uniprot_id", "disease_id", "drugbank_id", "protein_sequence"]:
        entities.setdefault(k, None)

    return entities


# ====================================================
# Node 3 — Graph Query
# ====================================================
def node_graph_query(intent: str, entities: Dict[str, Any], top_k: int):
    if intent not in ("protein_similarity", "disease_prediction", "drug_recommendation"):
        return None

    uid = entities.get("uniprot_id")
    if not uid:
        return None

    g = GraphSearchClient()
    try:
        if intent == "protein_similarity":
            return g.similar_proteins(uid, top_k)
        if intent == "disease_prediction":
            return g.predict_diseases(uid, top_k)
        if intent == "drug_recommendation":
            return g.recommend_drugs(uid, top_k)
    finally:
        g.close()


# ====================================================
# Node 3.5 — Relation Weighting
# ====================================================
def node_relation_weighting(intent: str, graph_result: Optional[List[Dict]]):
    if not graph_result:
        return graph_result

    if intent not in ("disease_prediction", "drug_recommendation"):
        return graph_result

    task = "disease_prediction" if intent == "disease_prediction" else "drug_recommendation"

    for r in graph_result:
        direct = r.get("direct_score", 0.0) or 0.0
        prop = r.get("propagated_score", 0.0) or 0.0
        r["total_score"] = relation_weighting.score(task, direct, prop)

    graph_result.sort(key=lambda x: x["total_score"], reverse=True)
    return graph_result


# ====================================================
# Node 4 — Evidence Path Node
# ====================================================
def node_evidence_paths(
    intent: str,
    entities: Dict[str, Any],
    graph_result: Optional[List[Dict[str, Any]]],
    top_k: int = 5,
):
    uid = entities.get("uniprot_id")
    if not uid:
        return None

    candidate, mode = None, None

    if intent == "disease_prediction":
        if graph_result:
            candidate = graph_result[0].get("disease_id")
            mode = "protein_disease"

    elif intent == "drug_recommendation":
        if graph_result:
            candidate = graph_result[0].get("drugbank_id")
            mode = "protein_drug"

    elif intent == "evidence_paths":
        if entities.get("disease_id"):
            candidate = entities["disease_id"]
            mode = "protein_disease"
        elif entities.get("drugbank_id"):
            candidate = entities["drugbank_id"]
            mode = "protein_drug"

    if not candidate:
        return None

    return evidence_node.run(uid, candidate, mode, top_k)


# ====================================================
# Node 5 — Web Crawlers
# ====================================================
def node_web_crawlers(question: str, intent: str):
    if intent == "protein_redesign":
        return None

    return {
        "wiki": fetch_wikipedia_summary(question),
        "pubchem": fetch_pubchem_info(question),
        "uniprot": fetch_uniprot_summary(question),
    }


# ====================================================
# Node 6 — Final Reasoning
# ====================================================
def node_answer(question, intent, entities, graph_result, evidence_paths, crawlers):
    if intent == "protein_redesign":
        seq = entities.get("protein_sequence")
        if not seq:
            return {"error": "protein_sequence not detected"}

        inp = ProteinRedesignInput(sequence=seq)
        return protein_redesign_node.run(inp).model_dump()

    ep_dump = None
    if evidence_paths:
        try:
            ep_dump = evidence_paths.model_dump()
        except:
            ep_dump = evidence_paths

    prompt = f"""
단백질-질병-약물 그래프 기반 Bio-AI 분석 결과를 요약하세요.

[질문]
{question}

[Intent]
{intent}

[Entities]
{json.dumps(entities, ensure_ascii=False)}

[Graph Results]
{json.dumps(graph_result or {}, ensure_ascii=False)}

[Evidence Paths]
{json.dumps(ep_dump or {}, ensure_ascii=False)}

[External Web Data]
{json.dumps(crawlers or {}, ensure_ascii=False)}

요구사항:
1) 생물학적/약리 메커니즘 설명
2) graph_result와 evidence_paths 근거 강조
3) 강한/약한 근거 구분
4) 한계점 및 추가 실험 제안
"""
    return _llm(prompt)


# ====================================================
# Workflow Runner
# ====================================================
def run_workflow(question: str, top_k: int = 10) -> Dict[str, Any]:
    intent = node_intent(question).get("intent", "general_search")
    entities = node_extract_entities(question)

    graph_result = node_graph_query(intent, entities, top_k)
    graph_result = node_relation_weighting(intent, graph_result)

    evidence_paths = node_evidence_paths(intent, entities, graph_result, top_k=5)

    crawlers = node_web_crawlers(question, intent)

    final_answer = node_answer(
        question, intent, entities, graph_result, evidence_paths, crawlers
    )

    return {
        "intent": intent,
        "entities": entities,
        "graph_result": graph_result,
        "evidence_paths": evidence_paths.model_dump() if hasattr(evidence_paths, "model_dump") else None,
        "crawlers": crawlers,
        "final_answer": final_answer,
    }


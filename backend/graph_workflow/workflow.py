# backend/graph_workflow/workflow.py
import os, json
from typing import Dict, Any

from openai import OpenAI
from backend.graph.graph_search_client import GraphSearchClient
from backend.crawlers.disease_wiki_crawler import fetch_wikipedia_summary
from backend.crawlers.pubchem_crawler import fetch_pubchem_info
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


# ====================================================
# Node 1 — Intent Classification
# ====================================================
def node_intent(question: str) -> Dict[str, Any]:
    prompt = f"""
    분류 가능한 Intent:
    - protein_similarity
    - disease_prediction
    - drug_recommendation
    - evidence_paths
    - general_search

    질문: {question}
    Intent 하나만 출력:
    """
    intent = _llm(prompt).strip()
    return {"intent": intent}


# ====================================================
# Node 2 — Entity Extraction
# ====================================================
def node_extract_entities(question: str) -> Dict[str, Any]:
    prompt = f"""
    질문에서 엔터티 추출:
    반환 JSON 키:
    - uniprot_id
    - disease_id
    - drugbank_id

    없는 값은 null.

    질문: {question}
    JSON만 출력:
    """
    try:
        raw = _llm(prompt)
        entities = json.loads(raw)
    except:
        entities = {}
    return entities


# ====================================================
# Node 3 — GraphDB Query
# ====================================================
def node_graph_query(intent: str, entities: Dict[str, Any], top_k: int):
    g = GraphSearchClient()

    try:
        if intent == "protein_similarity":
            return g.similar_proteins(entities.get("uniprot_id"), top_k)

        if intent == "disease_prediction":
            return g.predict_diseases(entities.get("uniprot_id"), top_k)

        if intent == "drug_recommendation":
            return g.recommend_drugs(entities.get("uniprot_id"), top_k)

        if intent == "evidence_paths":
            uid = entities.get("uniprot_id")
            did = entities.get("disease_id")
            drug = entities.get("drugbank_id")

            if did:
                return g.evidence_paths_protein_disease(uid, did)
            if drug:
                return g.evidence_paths_protein_drug(uid, drug)

    finally:
        g.close()

    return None


# ====================================================
# Node 4 — Crawlers
# ====================================================
def node_web_crawlers(question: str):
    wiki = fetch_wikipedia_summary(question)
    pubchem = fetch_pubchem_info(question)
    uniprot = fetch_uniprot_summary(question)

    return {
        "wiki": wiki,
        "pubchem": pubchem,
        "uniprot": uniprot,
    }


# ====================================================
# Node 5 — Answer Generation
# ====================================================
def node_answer(question: str, intent: str, entities, graph, crawlers):
    prompt = f"""
    사용자의 질문에 대해 아래 정보를 바탕으로 생물학적 분석을 자세히 설명하세요.

    질문: {question}

    Intent: {intent}
    Entities: {json.dumps(entities, ensure_ascii=False)}
    Graph Results: {json.dumps(graph, ensure_ascii=False)}
    Web Data: {json.dumps(crawlers, ensure_ascii=False)}

    위 정보를 종합해서:
    1) 의미 있는 과학적 해석
    2) 관계 설명
    3) 가능한 기능적 연관성
    4) 필요시 경고/한계

    를 포함해서 한국어로 답변하세요.
    """
    return _llm(prompt)


# ====================================================
# 내부 LLM Helper
# ====================================================
def _llm(prompt: str) -> str:
    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
    )
    return res.choices[0].message.content


# ====================================================
# Main Workflow Runner
# ====================================================
def run_workflow(question: str, top_k: int = 10) -> Dict[str, Any]:

    # Node 1
    intent_result = node_intent(question)
    intent = intent_result["intent"]

    # Node 2
    entities = node_extract_entities(question)

    # Node 3
    graph_result = node_graph_query(intent, entities, top_k)

    # Node 4
    crawler_result = node_web_crawlers(question)

    # Node 5
    answer = node_answer(
        question,
        intent,
        entities,
        graph_result,
        crawler_result,
    )

    return {
        "intent": intent,
        "entities": entities,
        "graph_result": graph_result,
        "crawlers": crawler_result,
        "final_answer": answer,
    }

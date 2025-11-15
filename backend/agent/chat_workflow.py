# backend/agent/chat_workflow.py

import os
from typing import TypedDict, Literal, Optional, List, Dict, Any

from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from backend.graph.graph_search_client import GraphSearchClient

# (선택) 크롤러들 필요하면 나중에 이쪽도 붙이면 됨
# from backend.crawlers.pubmed_crawler import fetch_pubmed_summaries
# from backend.crawlers.disease_wiki_crawler import fetch_wiki_summary

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(os.path.dirname(BASE_DIR), ".env")
load_dotenv(ENV_PATH)


# =========================
# 1. 상태 정의 (LangGraph State)
# =========================

class ChatState(TypedDict, total=False):
    query: str
    intent: Literal["protein_analysis", "disease_query", "drug_query", "design", "other"]
    protein_id: Optional[str]
    disease_id: Optional[str]
    drug_id: Optional[str]

    graph_results: Dict[str, Any]        # 질병예측 / 약물추천 / 유사단백질
    redesign_suggestions: Optional[Dict[str, Any]]
    evidence_paths: Optional[Dict[str, Any]]

    answer: str


# =========================
# 2. LLM & Graph Client
# =========================

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.2,
)

graph_client = GraphSearchClient()


# =========================
# 3. 노드 함수들
# =========================

def classify_intent(state: ChatState) -> ChatState:
    """사용자 질문에서 의도를 분류 + 단백질/질병/약물 ID 추출"""
    prompt = f"""
너는 바이오/약학 챗봇의 라우팅 담당자야.

사용자 질문:
{state["query"]}

아래 JSON 형식으로만 답해:
- intent: "protein_analysis" | "disease_query" | "drug_query" | "design" | "other"
- protein_id: 단백질 Uniprot ID 또는 심볼 (몰라도 null)
- disease_id: 질병 이름 또는 ID (몰라도 null)
- drug_id: 약물 이름 또는 ID (몰라도 null)
"""
    msg = llm.invoke([HumanMessage(content=prompt)])
    import json
    try:
        parsed = json.loads(msg.content)
    except Exception:
        parsed = {
            "intent": "other",
            "protein_id": None,
            "disease_id": None,
            "drug_id": None,
        }

    state["intent"] = parsed.get("intent", "other")
    state["protein_id"] = parsed.get("protein_id")
    state["disease_id"] = parsed.get("disease_id")
    state["drug_id"] = parsed.get("drug_id")
    return state


def run_graph_search(state: ChatState) -> ChatState:
    """단백질 기반 그래프 검색 (질병, 약, 유사 단백질)"""
    protein_id = state.get("protein_id")
    if not protein_id:
        # 단백질 ID가 없으면 패스
        state["graph_results"] = {}
        return state

    results: Dict[str, Any] = {}

    try:
        diseases = graph_client.predict_diseases(uniprot_id=protein_id, top_k=10)
        results["diseases"] = diseases
    except Exception as e:
        results["diseases_error"] = str(e)

    try:
        drugs = graph_client.recommend_drugs(uniprot_id=protein_id, top_k=10)
        results["drugs"] = drugs
    except Exception as e:
        results["drugs_error"] = str(e)

    try:
        sims = graph_client.similar_proteins(uniprot_id=protein_id, top_k=10)
        results["similar_proteins"] = sims
    except Exception as e:
        results["similar_error"] = str(e)

    state["graph_results"] = results
    return state


def design_protein(state: ChatState) -> ChatState:
    """
    AI 단백질 재설계 노드 (고수준 제안만 수행, 실험 프로토콜은 제공 X)
    - 기능 유지 / 안정성 향상 / 면역원성 감소 등 제안
    """
    protein_id = state.get("protein_id")
    graph_results = state.get("graph_results", {})

    prompt = f"""
너는 단백질 공학 AI 어시스턴트야.
단, 실험용 프로토콜(실험 조건, 농도, 구체적 lab 단계)는 절대 제안하지 말고,
오직 서열 수준의 고수준 변이 제안과 rationale만 설명해.

단백질 ID: {protein_id}
그래프 기반 컨텍스트(질병/약물/유사단백질 요약):

{graph_results}

1) 이 단백질의 주요 기능/역할을 먼저 추론하고,
2) 기능을 유지하면서 안정성 또는 약물 타깃 적합성을 높일 수 있는 point mutation 2~3개를 제안해.
3) 각 변이에 대해:
   - 원래 아미노산 -> 새로운 아미노산 (예: R175H)
   - 예상 효과 (예: 구조 안정성 증가, 리간드 결합력 증가)
   - 구조/전하/입체적 근거를 설명해.

주의:
- 실제 실험 조건, 세포주, 농도, 투여방법 등은 절대 이야기하지 마.
- 변이는 conceptual level에서만 제안해.
"""

    msg = llm.invoke([HumanMessage(content=prompt)])

    state["redesign_suggestions"] = {
        "protein_id": protein_id,
        "raw_text": msg.content,
    }
    return state


def build_evidence_paths(state: ChatState) -> ChatState:
    """
    근거 path 자동 생성:
    - 상위 1개 질병 / 1개 약물에 대해,
    - Protein → ... → Disease / Drug 경로를 Neo4j에서 추출
    """
    protein_id = state.get("protein_id")
    graph_results = state.get("graph_results") or {}

    evidence: Dict[str, Any] = {}

    # 상위 1개 질병 path
    diseases = graph_results.get("diseases") or []
    if protein_id and diseases:
        top_d = diseases[0]
        disease_id = top_d.get("disease_id")
        if disease_id:
            try:
                paths = graph_client.evidence_paths_protein_disease(
                    uniprot_id=protein_id,
                    disease_id=disease_id,
                    max_paths=3,
                    max_hops=4,
                )
                evidence["disease_paths"] = {
                    "disease_id": disease_id,
                    "paths": paths,
                }
            except Exception as e:
                evidence["disease_paths_error"] = str(e)

    # 상위 1개 약물 path
    drugs = graph_results.get("drugs") or []
    if protein_id and drugs:
        top_dr = drugs[0]
        drug_id = top_dr.get("drugbank_id")
        if drug_id:
            try:
                paths = graph_client.evidence_paths_protein_drug(
                    uniprot_id=protein_id,
                    drugbank_id=drug_id,
                    max_paths=3,
                    max_hops=4,
                )
                evidence["drug_paths"] = {
                    "drugbank_id": drug_id,
                    "paths": paths,
                }
            except Exception as e:
                evidence["drug_paths_error"] = str(e)

    state["evidence_paths"] = evidence
    return state


def compose_answer(state: ChatState) -> ChatState:
    """그래프 결과 + 재설계 제안 + 근거 path를 모두 묶어 자연어 답변 생성"""
    query = state["query"]
    intent = state.get("intent")
    protein_id = state.get("protein_id")

    graph_results = state.get("graph_results", {})
    redesign = state.get("redesign_suggestions")
    evidence_paths = state.get("evidence_paths")

    system = SystemMessage(content="""
너는 단백질-질병-약물-임상 그래프를 사용하는 바이오 AI 어시스턴트다.
사용자에게:
- 네트워크 기반 질병/약물 후보
- 왜 그런 결과가 나왔는지(근거 path 요약)
- 필요하다면 단백질 재설계 아이디어 (고수준 mutation 제안만)
을 한국어로, but 중요한 ID(uniprot, drugbank, nct 등)는 그대로 표시해.

실험 프로토콜/용량/세포주/동물실험 설계/인체 적용 등의 구체적인 실험 방법은 절대 설명하지 마라.
""")

    user = HumanMessage(content=f"""
사용자 질문: {query}

의도(intent): {intent}
단백질 ID: {protein_id}

그래프 검색 결과:
{graph_results}

단백질 재설계 제안 (LLM생성 텍스트):
{redesign}

근거 경로(evidence paths):
{evidence_paths}

위 정보를 요약해서:
1) 단백질의 주요 특징과 관련 질병/약물 후보
2) 네트워크 관점에서의 연결 이유 (단순하고 직관적으로)
3) (의도가 design일 때만) 재설계 mutation 제안 요약

형식:
- 마크다운 bullet 위주
- 너무 길지 않게, 하지만 핵심 근거는 꼭 포함
""")

    msg = llm.invoke([system, user])
    state["answer"] = msg.content
    return state


# =========================
# 4. LangGraph 그래프 정의
# =========================

def build_chat_graph():
    g = StateGraph(ChatState)

    g.add_node("classify_intent", classify_intent)
    g.add_node("graph_search", run_graph_search)
    g.add_node("design_protein", design_protein)
    g.add_node("build_evidence", build_evidence_paths)
    g.add_node("compose_answer", compose_answer)

    g.set_entry_point("classify_intent")

    # intent에 따라 design 노드 수행 여부는 compose_answer에서 참고해서 정리하므로
    # 그래프는 단순 직렬로 구성
    g.add_edge("classify_intent", "graph_search")
    g.add_edge("graph_search", "design_protein")
    g.add_edge("design_protein", "build_evidence")
    g.add_edge("build_evidence", "compose_answer")
    g.add_edge("compose_answer", END)

    return g.compile()


chat_graph = build_chat_graph()


def run_chat(query: str) -> str:
    """FastAPI나 Streamlit에서 호출할 high-level 함수"""
    initial_state: ChatState = {"query": query}
    final_state = chat_graph.invoke(initial_state)
    return final_state.get("answer", "")



# from backend.agent.chat_workflow import run_chat

# answer = run_chat("TP53 관련 암 질환이 뭐가 있고, 약물 후보랑 임상까지 연결해서 설명해줘")

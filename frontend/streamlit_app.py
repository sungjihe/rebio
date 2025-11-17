import os
import json
import requests
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import streamlit as st
import py3Dmol
import streamlit.components.v1 as components

# =========================
# 기본 설정
# =========================
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

st.set_page_config(
    page_title="ReBio Graph Reasoning UI",
    layout="wide",
)

st.title("🧠 ReBio – Graph-based Reasoning & Protein Redesign Dashboard")


# =========================
# 유틸 함수들
# =========================
def call_backend(path: str, method: str = "GET", json_body=None, params=None):
    url = f"{API_BASE}{path}"
    try:
        if method.upper() == "GET":
            res = requests.get(url, params=params, timeout=60)
        else:
            res = requests.post(url, json=json_body, timeout=120)
        res.raise_for_status()
        return res.json()
    except Exception as e:
        st.error(f"API 호출 실패: {url}\n{e}")
        return None


def draw_graph_from_visualization_json(vis_json: dict):
    """EvidencePath의 visualization_json을 NetworkX + matplotlib으로 렌더링"""
    if not vis_json:
        st.info("그래프 근거 데이터가 없습니다.")
        return

    G = nx.DiGraph()

    # vis_json: {"nodes":[{"data":{"id":..,"label":..}}, ...],
    #            "edges":[{"data":{"source":..,"target":..,"type":..}}, ...]}
    for n in vis_json.get("nodes", []):
        nid = n["data"]["id"]
        label = n["data"].get("label", nid)
        ntype = n["data"].get("type", "")
        G.add_node(nid, label=label, type=ntype)

    for e in vis_json.get("edges", []):
        src = e["data"]["source"]
        tgt = e["data"]["target"]
        etype = e["data"].get("type", "")
        G.add_edge(src, tgt, type=etype)

    if len(G.nodes) == 0:
        st.info("그래프 노드가 없습니다.")
        return

    # layout 및 그리기
    pos = nx.spring_layout(G, seed=42)
    plt.figure(figsize=(6, 6))
    nx.draw(
        G,
        pos,
        with_labels=False,
        node_size=500,
    )
    # label 별도
    labels = {n: d["label"] for n, d in G.nodes(data=True)}
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    st.pyplot(plt.gcf())
    plt.close()


def show_py3dmol_view(pdb_str: str):
    """PDB 문자열을 py3Dmol로 Streamlit에 표시"""
    if not pdb_str:
        st.info("PDB 구조 데이터가 없습니다.")
        return

    view = py3Dmol.view(width=500, height=500)
    view.addModel(pdb_str, "pdb")
    view.setStyle({"cartoon": {}})
    view.zoomTo()
    html = view._make_html()
    components.html(html, height=520)


def build_similarity_heatmap(similar_list, query_id: str):
    """
    similar_list: /protein/similar_proteins 응답 (list of {protein_id, similarity,...})
    query_id: 중심 단백질 ID
    """
    if not similar_list:
        st.info("유사 단백질 정보가 없습니다.")
        return

    # 간단하게 query를 포함한 1D heatmap 비슷하게 표현
    proteins = [query_id] + [item["protein_id"] for item in similar_list]
    sims = [1.0] + [item["similarity"] for item in similar_list]

    fig, ax = plt.subplots(figsize=(4, 6))
    im = ax.imshow(np.array(sims).reshape(-1, 1))
    ax.set_yticks(range(len(proteins)))
    ax.set_yticklabels(proteins, fontsize=8)
    ax.set_xticks([])
    ax.set_title("Cosine Similarity (query vs others)")
    st.pyplot(fig)
    plt.close()


# =========================
# 사이드바
# =========================
st.sidebar.header("⚙ 설정")
st.sidebar.write(f"Backend API: `{API_BASE}`")

st.sidebar.markdown("---")
st.sidebar.markdown("**사용 팁**")
st.sidebar.write(
    "- 자연어 질문을 넣으면 `/chat/run_workflow`를 호출해서 전체 그래프 기반 Reasoning 수행\n"
    "- 질문에 UniProt ID를 포함하면 Protein 분석/추천이 강화됩니다.\n"
    "- protein_redesign 의도가 담긴 질문(예: '이 서열을 안정성 높게 재설계해줘')은 재설계 모드로 동작합니다."
)

# =========================
# 메인 입력 영역
# =========================
st.markdown("## 🔍 질의 입력")

default_q = (
    "TP53 단백질과 연관된 암 질환과 약물 후보를 그래프 근거와 함께 설명해줘."
)
user_query = st.text_area("질문을 입력하세요:", value=default_q, height=80)

col_run, col_topk = st.columns([1, 1])
with col_topk:
    top_k = st.number_input("Top K (Graph/추천 상위 개수)", min_value=1, max_value=50, value=10)

with col_run:
    run_button = st.button("🚀 워크플로우 실행")

result = None
if run_button and user_query.strip():
    with st.spinner("그래프 기반 워크플로우 실행 중..."):
        payload = {"query": user_query, "top_k": top_k}
        result = call_backend("/chat/run_workflow", method="POST", json_body=payload)

# 반응 데이터 구조 안전 처리
workflow = None
if result and "intent" in result:
    # 예: run_workflow 직접 반환 vs {"status":"ok","result":...} 형태
    # routes_chat.py는 run_workflow의 리턴 그대로 전달하므로 result가 이미 workflow 결과일 가능성이 높음
    if "final_answer" in result:
        workflow = result
    elif "result" in result:
        workflow = result["result"]
else:
    if result and "result" in result:
        workflow = result["result"]

if workflow:
    intent = workflow.get("intent")
    entities = workflow.get("entities", {})
    graph_result = workflow.get("graph_result")
    evidence_paths = workflow.get("evidence_paths")
    crawlers = workflow.get("crawlers")
    final_answer = workflow.get("final_answer")
else:
    intent = None
    entities = {}
    graph_result = None
    evidence_paths = None
    crawlers = None
    final_answer = None

# =========================
# 탭 레이아웃
# =========================
st.markdown("## 📊 분석 결과")

tabs = st.tabs(
    [
        "🧠 LLM Reasoning",
        "🕸 Neo4j Graph Evidence",
        "📈 Similarity Heatmap",
        "💊 Drug / Disease 추천",
        "🧪 Clinical Trials",
        "🧬 3D 구조 (PDB)",
        "🧫 재설계 단백질 (Protein Redesign)",
    ]
)

# ---------------------------------
# 1) LLM Reasoning 탭
# ---------------------------------
with tabs[0]:
    st.subheader("LLM Reasoning 결과")

    st.write(f"**Intent:** `{intent}`")
    st.json(entities, expanded=False)

    if isinstance(final_answer, str):
        st.markdown("### 📝 모델 답변")
        st.write(final_answer)
    elif isinstance(final_answer, dict) and final_answer.get("intent") == "protein_redesign":
        st.markdown("### 🧬 재설계 결과 요약")
        st.json(final_answer)
    else:
        if final_answer is not None:
            st.json(final_answer)
        else:
            st.info("아직 워크플로우를 실행하지 않았거나 결과가 없습니다.")

# ---------------------------------
# 2) Neo4j Graph Evidence 탭
# ---------------------------------
with tabs[1]:
    st.subheader("Neo4j Graph Evidence 시각화")

    if evidence_paths and isinstance(evidence_paths, dict):
        st.markdown("**Evidence Paths (raw)**")
        st.json(evidence_paths, expanded=False)

        vis_json = evidence_paths.get("visualization_json")
        if vis_json:
            st.markdown("### 🕸 Graph Layout")
            draw_graph_from_visualization_json(vis_json)

        rationale = evidence_paths.get("llm_rationale")
        if rationale:
            st.markdown("### 📖 Evidence 기반 설명")
            st.write(rationale)
    else:
        st.info("Evidence path 데이터가 없습니다. (intent가 redesign이거나, path 검출이 없을 수 있음)")

# ---------------------------------
# 3) Similarity Heatmap 탭
# ---------------------------------
with tabs[2]:
    st.subheader("Cosine Similarity Heatmap")

    uni = entities.get("uniprot_id")
    if uni:
        st.write(f"**중심 단백질(쿼리):** `{uni}`")
        sim_res = call_backend(
            "/protein/similar_proteins",
            method="POST",
            json_body={"uniprot_id": uni, "top_k": top_k},
        )
        if sim_res:
            df_sim = pd.DataFrame(sim_res)
            st.dataframe(df_sim)

            st.markdown("### Heatmap (query vs others)")
            build_similarity_heatmap(sim_res, query_id=uni)
        else:
            st.info("유사 단백질 결과가 없습니다.")
    else:
        st.info("엔터티에서 UniProt ID를 찾을 수 없습니다. 질문에 UniProt ID를 포함해보세요.")

# ---------------------------------
# 4) Drug / Disease 추천 탭
# ---------------------------------
with tabs[3]:
    st.subheader("Drug / Disease 추천")

    uni = entities.get("uniprot_id")
    if uni:
        col_d1, col_d2 = st.columns(2)

        # Disease prediction
        with col_d1:
            st.markdown("### 🩺 Disease Prediction")
            dis_res = call_backend(
                "/protein/predict_disease",
                method="POST",
                json_body={"uniprot_id": uni, "top_k": top_k},
            )
            if dis_res:
                df_dis = pd.DataFrame(dis_res)
                st.dataframe(df_dis)
            else:
                st.info("질병 예측 결과가 없습니다.")

        # Drug recommendation
        with col_d2:
            st.markdown("### 💊 Drug Recommendation")
            drug_res = call_backend(
                "/protein/recommend_drugs",
                method="POST",
                json_body={"uniprot_id": uni, "top_k": top_k},
            )
            if drug_res:
                df_drug = pd.DataFrame(drug_res)
                st.dataframe(df_drug)
            else:
                st.info("약물 추천 결과가 없습니다.")
    else:
        st.info("엔터티에서 UniProt ID를 찾을 수 없습니다.")

# ---------------------------------
# 5) Clinical Trials 탭
# ---------------------------------
with tabs[4]:
    st.subheader("Clinical Trials (NCT)")

    disease_id = entities.get("disease_id")
    query_for_trials = disease_id or user_query

    if run_button:
        st.write(f"검색 쿼리: `{query_for_trials}`")
        trials = call_backend(
            "/external/clinical_trials/search",
            method="GET",
            params={"query": query_for_trials, "max_results": 5},
        )
        if trials:
            if isinstance(trials, list):
                df_trials = pd.DataFrame(trials)
                st.dataframe(df_trials)
            else:
                st.json(trials)
        else:
            st.info("임상시험 결과가 없습니다.")
    else:
        st.info("먼저 상단에서 워크플로우를 실행해주세요.")

# ---------------------------------
# 6) 3D 구조 (PDB) 탭
# ---------------------------------
with tabs[5]:
    st.subheader("3D 구조 (PDB, py3Dmol)")

    # 1) 엔터티에서 PDB ID를 뽑아낼 수 있다면 활용 (지금은 유저 입력으로 처리)
    pdb_id_input = st.text_input("PDB ID를 직접 입력하세요 (예: 1TUP)", "")

    if pdb_id_input:
        with st.spinner(f"PDB {pdb_id_input} 구조 불러오는 중..."):
            try:
                pdb_url = f"https://files.rcsb.org/download/{pdb_id_input}.pdb"
                pdb_res = requests.get(pdb_url, timeout=30)
                pdb_res.raise_for_status()
                pdb_str = pdb_res.text
                show_py3dmol_view(pdb_str)
            except Exception as e:
                st.error(f"PDB 다운로드 실패: {e}")
    else:
        st.info("PDB ID를 입력하면 3D 구조를 볼 수 있습니다.")

# ---------------------------------
# 7) 재설계 단백질 탭
# ---------------------------------
with tabs[6]:
    st.subheader("재설계 단백질 (Protein Redesign Node Output)")

    if intent == "protein_redesign" and isinstance(final_answer, dict):
        redesign = final_answer.get("redesign_result", {})

        original_seq = redesign.get("original_sequence")
        original_score = redesign.get("original_score")
        variants = redesign.get("variants", [])

        st.markdown("### 원본 서열")
        st.code(original_seq or "(none)", language="text")
        st.write(f"**ESM2 score (원본):** {original_score}")

        if variants:
            st.markdown("### 재설계 변이 리스트")
            df_var = pd.DataFrame(variants)
            st.dataframe(df_var)

            # 첫 번째 변이 선택해서 서열/설명 보여주기
            st.markdown("### 상위 변이 상세")
            idx = st.number_input(
                "상세히 볼 변이 index (0-based)", min_value=0, max_value=len(variants) - 1, value=0
            )
            v = variants[idx]
            st.write(f"- Δscore: {v.get('delta_score')}")
            st.write(f"- predicted_stability: {v.get('predicted_stability')}")
            st.write(f"- rationale: {v.get('llm_rationale')}")
            st.markdown("**Redesigned sequence**")
            st.code(v.get("redesigned_sequence", ""), language="text")
        else:
            st.info("재설계 변이가 없습니다.")
    else:
        st.info("현재 Intent가 `protein_redesign`이 아니거나, 재설계 결과가 없습니다.")


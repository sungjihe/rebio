# streamlit_app/GraphAssistant.py

import os
import json
import requests
import streamlit as st
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
import streamlit.components.v1 as components

from utils_3d import render_3d_structure, render_mutation_overlay
from backend.utils.structure_loader import load_pdb_text


# ============================================================
# 환경 설정
# ============================================================
load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


# ============================================================
# UI 기본 세팅
# ============================================================
st.set_page_config(
    page_title="ReBio Graph Assistant",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 ReBio: Graph Intelligence Assistant")
st.caption("Protein–Disease–Drug Knowledge Graph + Evidence Reasoning + 3D Structure")


# ============================================================
# 사이드바 옵션
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    query_type = st.radio(
        "Query Type",
        ["Auto", "Protein", "Disease", "Drug"],
        index=0
    )

    top_k = st.slider("Top-K Graph Results", 5, 50, 10, 5)

    st.markdown("---")
    st.markdown("**Backend API URL**")
    st.code(FASTAPI_URL)


# ============================================================
# 사용자 질문
# ============================================================
question = st.text_area(
    "Ask a question about proteins, diseases, drugs, or interactions:",
    height=100,
    placeholder="예: 'EGFR와 관련된 암 질환과 약물 후보를 알려줘'"
)

run_btn = st.button("🚀 Run Analysis", type="primary")


# ============================================================
# API 호출 함수
# ============================================================
def call_api(query: str):
    try:
        res = requests.post(
            f"{FASTAPI_URL}/chat/run_workflow",
            json={"query": query, "top_k": top_k},
            timeout=180
        )
    except Exception as e:
        st.error(f"❌ Backend connection failed: {e}")
        return None

    if res.status_code != 200:
        st.error(f"❌ API Error {res.status_code}: {res.text}")
        return None

    try:
        return res.json()
    except:
        st.error("❌ JSON parsing failed")
        return None


# ============================================================
# 실행
# ============================================================
if run_btn:
    if not question.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    with st.spinner("⏳ Running multi-agent analysis..."):
        data = call_api(question)

    if not data:
        st.stop()

    # 해석
    intent = data.get("intent")
    entities = data.get("entities", {})
    graph_result = data.get("graph_result")
    evidence_paths = data.get("evidence_paths")
    crawlers = data.get("crawlers")
    final_answer = data.get("final_answer")
    design = data.get("design_result")
    pdb_text = data.get("pdb_text")

    # ========================================================
    # 상단: 모델 요약 보고서
    # ========================================================
    st.markdown("## 🧠 Scientific Summary")

    if isinstance(final_answer, str):
        st.markdown(final_answer)
    elif isinstance(final_answer, dict):
        summary = final_answer.get("summary_markdown")
        if summary:
            st.markdown(summary)
        else:
            st.json(final_answer)
    else:
        st.info("모델 요약 응답이 없습니다.")

    st.markdown("---")

    # ========================================================
    # TAB UI
    # ========================================================
    tab_graph, tab_evidence, tab_3d, tab_redesign, tab_external = st.tabs(
        ["📊 Graph Ranking", "🧩 Evidence", "🧬 3D Structure", "🧪 Redesign", "🔎 External Knowledge"]
    )

    # ------------------------------- TAB 1: Graph Ranking
    with tab_graph:
        st.subheader("📊 Graph Ranking Result")
        if graph_result:
            df = pd.DataFrame(graph_result)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No graph ranking result available.")

    # ------------------------------- TAB 2: Evidence Graph
    with tab_evidence:
        st.subheader("🧩 Evidence Graph")
        vis = (evidence_paths or {}).get("visualization_json")
        rationale = (evidence_paths or {}).get("llm_rationale")

        if rationale:
            st.markdown("### 🔍 LLM Rationale")
            st.write(rationale)

        if vis:
            html = f"""
            <div id="cy" style="width: 100%; height: 500px;"></div>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.22.2/cytoscape.min.js"></script>
            <script>
            var cy = cytoscape({{
                container: document.getElementById('cy'),
                elements: {json.dumps(vis)},
                style: [
                    {{
                        selector: 'node',
                        style: {{
                            'label': 'data(label)',
                            'background-color': '#9ecae1',
                            'color': '#222',
                            'font-size': '10px'
                        }}
                    }},
                    {{
                        selector: 'edge',
                        style: {{
                            'curve-style': 'bezier',
                            'target-arrow-shape': 'triangle',
                            'label': 'data(type)',
                            'font-size': '8px'
                        }}
                    }}
                ],
                layout: {{ name: 'cose' }}
            }});
            </script>
            """
            components.html(html, height=520)
        else:
            st.info("No evidence graph available.")

    # ------------------------------- TAB 3: 3D Structure
    with tab_3d:
        st.subheader("🧬 Protein 3D Structure")

        uid = entities.get("uniprot_id")
        if pdb_text:
            render_3d_structure(pdb_text, title=f"Predicted Structure ({uid})")
        else:
            if uid:
                text = load_pdb_text(uid)
                if text:
                    render_3d_structure(text, title=f"Structure ({uid})")
                else:
                    st.warning(f"No structure found for {uid}.")
            else:
                st.info("유니프로트 단백질이 감지되지 않았습니다.")

    # ------------------------------- TAB 4: Redesign
    with tab_redesign:
        st.subheader("🧪 Redesigned Variants")
        if design and isinstance(design, dict):
            variants = design.get("variants", [])
            if variants:
                df = pd.DataFrame(variants)
                st.dataframe(df, use_container_width=True)

                idx = st.selectbox(
                    "Highlight Variant",
                    list(range(len(variants))),
                    format_func=lambda i: variants[i].get("mutation_description", "variant")
                )

                variant = variants[idx]
                positions = variant.get("mutation_positions", [])

                if pdb_text and positions:
                    render_mutation_overlay(pdb_text, positions)

                st.json(variant)
            else:
                st.info("No redesign variants.")
        else:
            st.info("Redesign data not available.")

    # ------------------------------- TAB 5: External knowledge
    with tab_external:
        st.subheader("🔎 External Knowledge")
        st.json(crawlers)

    # Raw debug
    with st.expander("🔍 Raw JSON"):
        st.json(data)


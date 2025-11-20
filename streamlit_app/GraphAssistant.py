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

st.set_page_config(
    page_title="ReBio Graph Assistant",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 ReBio: Graph Intelligence Assistant")
st.caption("Protein–Disease–TherapeuticProtein Knowledge Graph + Evidence Reasoning + 3D Structure")


# ============================================================
# Sidebar Settings
# ============================================================
with st.sidebar:
    st.markdown("### ⚙️ Settings")

    query_type = st.radio(
        "Query Type (hint only, backend auto-intents)",
        ["Auto", "Protein", "Disease", "TherapeuticProtein"],
        index=0
    )

    top_k = st.slider("Top-K Graph Results (display only)", 5, 50, 10, 5)

    st.markdown("---")
    st.markdown("**Backend API URL**")
    st.code(f"{FASTAPI_URL}/rebio/run")


# ============================================================
# User Question
# ============================================================
question = st.text_area(
    "Ask a question about proteins, diseases, or therapeutic proteins:",
    height=100,
    placeholder="예: 'EGFR와 관련된 암 질환과 치료용 단백질 후보를 알려줘'"
)

run_btn = st.button("🚀 Run Analysis", type="primary")


# ============================================================
# API Call
# ============================================================
def call_api(query: str):
    """Call /rebio/run API"""
    payload = {"question": query}

    try:
        res = requests.post(
            f"{FASTAPI_URL}/rebio/run",
            json=payload,
            timeout=240,
        )
    except Exception as e:
        st.error(f"❌ Backend connection failed: {e}")
        return None

    if res.status_code != 200:
        st.error(f"❌ API Error {res.status_code}: {res.text}")
        return None

    try:
        return res.json()
    except Exception:
        st.error("❌ JSON parsing failed")
        return None


# ============================================================
# RUN WORKFLOW
# ============================================================
if run_btn:
    if not question.strip():
        st.warning("질문을 입력하세요.")
        st.stop()

    # ---------------- Progress UI (NEW) ----------------
    with st.status("🚀 Running ReBio Multi-Agent Workflow...", expanded=True) as status:

        progress_box = st.empty()
        progress_box.write("🔍 Step 1: Classifying intent...")

        # 실제 실행
        raw_data = call_api(question)

        if not raw_data:
            status.update(label="❌ Failed", state="error")
            st.stop()

        # FinalNode 기반 parsing
        if isinstance(raw_data, dict) and "final_output" in raw_data:
            data = raw_data["final_output"]
        else:
            data = raw_data

        # Backend history가 있다면 단계별 진행 상황 표시
        if isinstance(raw_data, dict) and raw_data.get("history"):
            for h in raw_data["history"]:
                node = h.get("node")
                if node:
                    progress_box.write(f"➡️ {node} completed")

        status.update(label="🎉 Completed", state="complete", expanded=False)

    # ============================================================
    # Extract data
    # ============================================================
    intent = data.get("intent")
    entities = data.get("entities", {}) or {}

    graph_result = data.get("graph_result")
    evidence_paths = data.get("evidence_paths")
    enriched_data = data.get("enriched_data")
    designed = data.get("designed_protein")
    structure = data.get("structure_result")
    vision = data.get("vision_data")

    reasoning_summary = data.get("reasoning_summary")
    reasoning_scientific = data.get("reasoning_scientific")

    markdown_summary = (
        data.get("markdown_summary")
        or reasoning_summary
    )

    pdb_text = None
    if isinstance(structure, dict):
        pdb_text = (
            structure.get("pdb_text")
            or structure.get("pdb")
            or structure.get("pdb_str")
        )


    # ============================================================
    # Summary Section
    # ============================================================
    st.markdown("## 🧠 Scientific Summary")

    if markdown_summary:
        st.markdown(markdown_summary)
    else:
        st.info("No markdown summary returned.")

    with st.expander("📌 Detected Intent & Entities"):
        st.write(f"**Intent:** `{intent}`")
        st.json(entities)

    st.markdown("---")


    # ============================================================
    # TABS
    # ============================================================
    tab_graph, tab_evidence, tab_3d, tab_redesign, tab_external, tab_raw = st.tabs(
        [
            "📊 Graph Ranking",
            "🧩 Evidence",
            "🧬 3D Structure",
            "🧪 Redesign",
            "🔎 External Knowledge",
            "🔍 Raw JSON",
        ]
    )

    # --------------------------------------------------------
    # TAB 1 Graph Ranking
    # --------------------------------------------------------
    with tab_graph:
        st.subheader("📊 Graph Ranking Result")
        if graph_result:
            try:
                df = pd.DataFrame(graph_result)
                st.dataframe(df, use_container_width=True)
            except Exception:
                st.json(graph_result)
        else:
            st.info("No graph_result returned.")


    # --------------------------------------------------------
    # TAB 2 Evidence
    # --------------------------------------------------------
    with tab_evidence:
        st.subheader("🧩 Evidence")

        if evidence_paths:
            if isinstance(evidence_paths, list):
                df_ev = pd.DataFrame(evidence_paths)
                st.dataframe(df_ev, use_container_width=True)

            elif isinstance(evidence_paths, dict):
                rationale = evidence_paths.get("llm_rationale")
                vis = evidence_paths.get("visualization_json")

                if rationale:
                    st.markdown("### 🧠 LLM Rationale")
                    st.write(rationale)

                if vis:
                    st.markdown("### 🌐 Graph Visualization")
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
            st.info("No evidence_paths returned.")


    # --------------------------------------------------------
    # TAB 3 Structure
    # --------------------------------------------------------
    with tab_3d:
        st.subheader("🧬 3D Structure")

        uid = entities.get("uniprot_id")

        if pdb_text:
            render_3d_structure(pdb_text, title=f"Predicted Structure ({uid or 'Unknown'})")
        else:
            if uid:
                text = load_pdb_text(uid)
                if text:
                    render_3d_structure(text, title=f"Structure From Local Store ({uid})")
                else:
                    st.warning(f"No structure found for {uid}.")
            else:
                st.info("유니프로트 ID가 감지되지 않았습니다.")


    # --------------------------------------------------------
    # TAB 4 Redesign
    # --------------------------------------------------------
    with tab_redesign:
        st.subheader("🧪 Redesigned Variants")
        variants = designed if isinstance(designed, list) else []

        if variants:
            df = pd.DataFrame(variants)
            st.dataframe(df, use_container_width=True)

            idx = st.selectbox(
                "Highlight Variant",
                list(range(len(variants))),
                format_func=lambda i: variants[i].get("mutation_description", f"Variant #{i+1}")
            )
            variant = variants[idx]
            st.json(variant)

            pos = variant.get("mutation_positions") or []
            if pdb_text and pos:
                render_mutation_overlay(pdb_text, pos)
        else:
            st.info("No redesigned variants returned.")


    # --------------------------------------------------------
    # TAB 5 External Knowledge
    # --------------------------------------------------------
    with tab_external:
        st.subheader("🔎 External Knowledge")
        if enriched_data:
            st.json(enriched_data)
        else:
            st.info("No enriched_data returned.")

        if vision:
            st.markdown("---")
            st.markdown("### 👁 Vision Evidence")
            st.json(vision)


    # --------------------------------------------------------
    # TAB 6 Raw JSON
    # --------------------------------------------------------
    with tab_raw:
        st.json(data)
        st.markdown("---")
        st.json(raw_data)


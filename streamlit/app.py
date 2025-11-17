# streamlit/app.py

import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import py3Dmol

# ----------------------------------------------------
# 0) Python path 설정 (backend import 가능하게)
# ----------------------------------------------------
BASE_DIR = Path(__file__).resolve().parents[1]  # /workspace/rebio
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

from backend.utils.structure_loader import load_pdb_text  # noqa


API_URL = os.getenv("REBIO_API_URL", "http://localhost:8000/chat/run_workflow")

st.set_page_config(
    page_title="ReBio Graph AI Assistant",
    page_icon="🧬",
    layout="wide",
)


# ----------------------------------------------------
# Helper: API 호출
# ----------------------------------------------------
def call_workflow_api(query: str, top_k: int = 10) -> Optional[Dict[str, Any]]:
    try:
        res = requests.post(
            API_URL,
            json={"query": query, "top_k": top_k},
            timeout=120,
        )
    except Exception as e:
        st.error(f"API 호출 실패: {e}")
        return None

    if res.status_code != 200:
        st.error(f"API 오류: {res.status_code} - {res.text}")
        return None

    try:
        return res.json()
    except Exception as e:
        st.error(f"응답 JSON 파싱 오류: {e}")
        return None


# ----------------------------------------------------
# Helper: Graph Result Table
# ----------------------------------------------------
def render_graph_ranking(intent: str, graph_result: Any):
    st.subheader("📊 그래프 기반 랭킹 결과")

    if not graph_result:
        st.info("그래프 결과가 없습니다.")
        return

    # 리스트 형태라고 가정
    if not isinstance(graph_result, list):
        st.json(graph_result)
        return

    df = pd.DataFrame(graph_result)

    if intent == "disease_prediction":
        st.markdown("**단백질 → 질병 예측 랭킹**")
    elif intent == "drug_recommendation":
        st.markdown("**단백질 → 약물 추천 랭킹**")
    elif intent == "protein_similarity":
        st.markdown("**유사 단백질 랭킹**")
    else:
        st.markdown("**그래프 랭킹 결과**")

    st.dataframe(df, use_container_width=True)


# ----------------------------------------------------
# Helper: Cytoscape Evidence Graph
# ----------------------------------------------------
def render_evidence_graph(ep: Dict[str, Any]):
    st.subheader("🧩 Evidence Graph (Neo4j Paths)")

    if not ep:
        st.info("Evidence path 결과가 없습니다.")
        return

    vis = ep.get("visualization_json")
    rationale = ep.get("llm_rationale")

    if rationale:
        st.markdown("**🧠 LLM 근거 설명:**")
        st.write(rationale)

    if not vis:
        st.info("시각화용 그래프 데이터가 없습니다.")
        return

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
              'text-valign': 'center',
              'color': '#222',
              'background-color': '#9ecae1',
              'font-size': '10px'
            }}
          }},
          {{
            selector: 'edge',
            style: {{
              'curve-style': 'bezier',
              'target-arrow-shape': 'triangle',
              'label': 'data(type)',
              'font-size': '8px',
              'line-color': '#aaa',
              'target-arrow-color': '#aaa'
            }}
          }}
        ],
        layout: {{ name: 'cose' }}
      }});
    </script>
    """
    components.html(html, height=520)


# ----------------------------------------------------
# Helper: py3Dmol 뷰 생성
# ----------------------------------------------------
def render_pdb_view(pdb_text: str, title: str = "Protein Structure"):
    view = py3Dmol.view(width=700, height=500)
    view.addModel(pdb_text, "pdb")
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.addStyle({"hetflag": True}, {"stick": {}})
    view.zoomTo()
    html = view._make_html()
    st.markdown(f"**{title}**", help="원본 3D 구조")
    components.html(html, height=520)


def render_mutation_overlay(
    pdb_text: str,
    original_seq: str,
    variant: Dict[str, Any],
    title: str = "Mutational Overlay (Original vs Variant)",
):
    """
    실제로는 동일 구조 위에서 변이 위치를 색상으로 강조.
    (새로운 구조 예측은 별도 파이프라인 필요)
    """
    positions = variant.get("mutation_positions", [])
    mut_desc = variant.get("mutation_description", "N/A")
    stability = variant.get("predicted_stability", "N/A")
    delta = variant.get("delta_score", 0.0)

    view = py3Dmol.view(width=700, height=500)
    # base model (grey)
    view.addModel(pdb_text, "pdb")
    view.setStyle({"cartoon": {"color": "lightgrey"}})

    # highlight mutated residues
    for pos in positions:
        # PDB의 resi는 1부터 시작한다고 가정
        view.addStyle(
            {"resi": int(pos)},
            {"stick": {"color": "red"}, "cartoon": {"color": "red"}},
        )

    view.zoomTo()
    html = view._make_html()

    st.markdown(f"**{title}**")
    st.markdown(
        f"- 🔁 변이: `{mut_desc}`  \n"
        f"- 🧪 안정성 예측: `{stability}`  \n"
        f"- Δscore (variant - wt): `{delta:.4f}`"
    )
    st.caption("※ 구조 좌표는 wild-type 기반이며, 변이 위치만 색상으로 강조됩니다.")
    components.html(html, height=520)

    # 간단한 alignment panel (길이가 같다고 가정)
    redesigned_seq = variant.get("redesigned_sequence", "")
    if redesigned_seq and len(redesigned_seq) == len(original_seq):
        st.markdown("**🧬 Sequence Alignment (WT vs Variant)**")
        st.text(make_simple_alignment(original_seq, redesigned_seq))


def make_simple_alignment(seq1: str, seq2: str) -> str:
    """
    Clustal-like 간단 alignment 표현 (길이 동일한 경우)
    ex)
    WT:  MEEPQSDPSVEPPLSQETF...
         |||  |  ||  |
    Var: MEEPASDASVEPALNQETF...
    """
    line1 = []
    line2 = []
    mid = []

    for a, b in zip(seq1, seq2):
        line1.append(a)
        line2.append(b)
        mid.append("|" if a == b else " ")

    s1 = "WT : " + "".join(line1)
    s2 = "VAR: " + "".join(line2)
    sm = "     " + "".join(mid)
    return "\n".join([s1, sm, s2])


# ----------------------------------------------------
# Helper: Redesign Panel
# ----------------------------------------------------
def render_redesign_panel(final_answer: Any):
    """
    workflow의 final_answer가 protein_redesign 모드일 때
    redesign_result를 테이블 + 선택 UI로 렌더링.
    """
    if not isinstance(final_answer, dict):
        st.info("재설계 결과가 없습니다.")
        return

    if final_answer.get("intent") != "protein_redesign":
        st.info("현재 Intent는 protein_redesign가 아닙니다.")
        return

    redesign = final_answer.get("redesign_result")
    if not redesign:
        st.info("redesign_result가 비어 있습니다.")
        return

    original_seq = redesign.get("original_sequence", "")
    variants = redesign.get("variants", [])

    st.markdown("### 🧬 Protein Redesign 결과")

    if not variants:
        st.warning("생성된 변이 서열이 없습니다.")
        return

    # 테이블용 데이터프레임
    df = pd.DataFrame(
        [
            {
                "redesigned_sequence": v.get("redesigned_sequence", ""),
                "num_mutations": v.get("num_mutations", 0),
                "delta_score": v.get("delta_score", 0.0),
                "predicted_stability": v.get("predicted_stability", ""),
                "mutation_description": v.get("mutation_description", ""),
            }
            for v in variants
        ]
    )
    st.dataframe(df, use_container_width=True)

    # 개별 variant 선택
    idx = st.selectbox(
        "3D 하이라이트에 사용할 변이 선택",
        options=list(range(len(variants))),
        format_func=lambda i: f"#{i} - {variants[i].get('mutation_description', 'variant')}",
    )
    return original_seq, variants[idx]


# ----------------------------------------------------
# Helper: 외부 지식 패널
# ----------------------------------------------------
def render_external_knowledge(crawlers: Any):
    st.subheader("🔎 External Knowledge (Web Crawlers)")

    if crawlers is None:
        st.info("크롤러 데이터가 없습니다.")
        return

    wiki = crawlers.get("wiki")
    pubchem = crawlers.get("pubchem")
    uniprot = crawlers.get("uniprot")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**📚 Wikipedia / Disease**")
        if wiki:
            st.write(wiki)
        else:
            st.caption("데이터 없음")

    with col2:
        st.markdown("**💊 PubChem / Drug**")
        if pubchem:
            st.json(pubchem)
        else:
            st.caption("데이터 없음")

    with col3:
        st.markdown("**🧬 UniProt / Protein**")
        if uniprot:
            st.json(uniprot)
        else:
            st.caption("데이터 없음")


# ----------------------------------------------------
# MAIN UI
# ----------------------------------------------------
st.title("🧬 ReBio Graph AI Assistant")
st.caption("Protein–Disease–Drug Graph + Evidence + 3D Structure + Redesign")

with st.sidebar:
    st.markdown("### ⚙️ 설정")
    top_k = st.slider("Top-K 결과 수", min_value=5, max_value=50, value=10, step=5)
    st.markdown("---")
    st.markdown("**API 엔드포인트**")
    st.text(API_URL)

query = st.text_area("질문을 입력하세요", height=80, placeholder="예: P04637 단백질과 관련된 암 질환과 약물 추천을 설명해줘")

if st.button("Run Analysis", type="primary"):
    if not query.strip():
        st.warning("질문을 입력하세요.")
    else:
        with st.spinner("그래프 검색 + Evidence 추출 + Reasoning 중..."):
            data = call_workflow_api(query, top_k=top_k)

        if data is None:
            st.stop()

        # top-level unpack
        intent = data.get("intent", "general_search")
        entities = data.get("entities", {})
        graph_result = data.get("graph_result")
        evidence_paths = data.get("evidence_paths")
        crawlers = data.get("crawlers")
        final_answer = data.get("final_answer")

        # ------------------------------------------------
        # 상단: 자연어 답변
        # ------------------------------------------------
        st.markdown("## 🧠 모델 해석 결과")

        if isinstance(final_answer, str):
            st.write(final_answer)
        else:
            # protein_redesign 모드일 경우 final_answer 자체가 dict
            st.json(final_answer)

        st.markdown("---")

        # 탭 구성
        tab_graph, tab_evidence, tab_3d, tab_redesign, tab_external = st.tabs(
            [
                "📊 Graph Ranking",
                "🧩 Evidence Graph",
                "🧫 3D Structure & Mutations",
                "🧪 Redesign Details",
                "🔎 External Knowledge",
            ]
        )

        # ------------------------------------------------
        # Tab 1: Graph Ranking
        # ------------------------------------------------
        with tab_graph:
            render_graph_ranking(intent, graph_result)

        # ------------------------------------------------
        # Tab 2: Evidence Graph
        # ------------------------------------------------
        with tab_evidence:
            render_evidence_graph(evidence_paths or {})

        # ------------------------------------------------
        # Tab 3: 3D Structure & Mutations
        # ------------------------------------------------
        with tab_3d:
            uid = entities.get("uniprot_id")
            if not uid:
                st.info("질문에서 UniProt ID(uniprot_id)를 찾을 수 없어 3D 구조를 표시할 수 없습니다.")
            else:
                pdb_text = load_pdb_text(uid)
                if not pdb_text:
                    st.error(f"{uid}에 대한 PDB/AlphaFold 구조를 가져오지 못했습니다.")
                else:
                    col_left, col_right = st.columns(2)

                    with col_left:
                        render_pdb_view(pdb_text, title=f"Original Structure ({uid})")

                    with col_right:
                        # redesign 결과가 있는 경우에만 overlay 표시
                        original_seq, chosen_variant = None, None
                        if isinstance(final_answer, dict) and final_answer.get("intent") == "protein_redesign":
                            tmp = render_redesign_panel(final_answer)  # returns (orig_seq, variant) or None
                            if tmp is not None:
                                original_seq, chosen_variant = tmp

                        # 재설계 결과가 없으면 안내
                        if not (original_seq and chosen_variant):
                            st.info("재설계 변이 정보가 없어서 변이 overlay는 표시하지 않습니다.")
                        else:
                            render_mutation_overlay(
                                pdb_text=pdb_text,
                                original_seq=original_seq,
                                variant=chosen_variant,
                            )

        # ------------------------------------------------
        # Tab 4: Redesign Details
        # ------------------------------------------------
        with tab_redesign:
            render_redesign_panel(final_answer)

        # ------------------------------------------------
        # Tab 5: External Knowledge
        # ------------------------------------------------
        with tab_external:
            render_external_knowledge(crawlers)

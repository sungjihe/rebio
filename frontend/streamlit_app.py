import streamlit as st
import requests
import py3Dmol

API_BASE = "http://localhost:8000"  # FastAPI 주소

st.set_page_config(page_title="ReBio Graph Assistant", layout="wide")

st.title("🧬 ReBio Graph Assistant")

tab1, tab2, tab3 = st.tabs(["질문 기반 챗봇", "그래프 요약", "PDB 3D 뷰어"])

# =========================
# 1) 질문 기반 챗봇 (LangGraph)
# =========================
with tab1:
    st.subheader("그래프 + 재설계 기반 챗봇")

    user_query = st.text_area("질문을 입력하세요", height=120)

    if st.button("질문 보내기"):
        if not user_query.strip():
            st.warning("질문을 입력해 주세요.")
        else:
            # FastAPI에 /chat/query 같은 엔드포인트를 만들었다고 가정
            try:
                resp = requests.post(
                    f"{API_BASE}/chat/query",
                    json={"query": user_query},
                    timeout=60,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown(data.get("answer", "_no answer_"))
                else:
                    st.error(f"API error: {resp.status_code} - {resp.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

# =========================
# 2) 그래프 요약 (단백질 ID 기반)
# =========================
with tab2:
    st.subheader("단백질 기반 그래프 요약")

    col_left, col_right = st.columns([1, 2])
    with col_left:
        protein_id = st.text_input("Uniprot ID", value="P04637")

        if st.button("그래프 요약 불러오기"):
            try:
                sims = requests.post(
                    f"{API_BASE}/protein/similar_proteins",
                    json={"uniprot_id": protein_id, "top_k": 10},
                    timeout=30,
                ).json()

                diseases = requests.post(
                    f"{API_BASE}/protein/predict_disease",
                    json={"uniprot_id": protein_id, "top_k": 10},
                    timeout=30,
                ).json()

                drugs = requests.post(
                    f"{API_BASE}/protein/recommend_drugs",
                    json={"uniprot_id": protein_id, "top_k": 10},
                    timeout=30,
                ).json()

                st.session_state["last_graph"] = {
                    "similar": sims,
                    "diseases": diseases,
                    "drugs": drugs,
                }

            except Exception as e:
                st.error(f"Error: {e}")

    with col_right:
        graph_data = st.session_state.get("last_graph")
        if graph_data:
            st.markdown("### 유사 단백질")
            st.json(graph_data["similar"])

            st.markdown("### 관련 질병 후보")
            st.json(graph_data["diseases"])

            st.markdown("### 약물 추천")
            st.json(graph_data["drugs"])
        else:
            st.info("왼쪽에서 단백질 ID를 입력하고 '그래프 요약 불러오기'를 눌러주세요.")

# =========================
# 3) PDB 3D 뷰어 (py3Dmol)
# =========================
with tab3:
    st.subheader("PDB 구조 3D 시각화")

    pdb_id = st.text_input("PDB ID (예: 1TUP)", value="1TUP")

    if st.button("PDB 로드"):
        if not pdb_id.strip():
            st.warning("PDB ID를 입력해 주세요.")
        else:
            view = py3Dmol.view(query=f"pdb:{pdb_id}")
            view.setStyle({"cartoon": {"color": "spectrum"}})
            view.zoomTo()

            # Streamlit에 렌더
            st.components.v1.html(view._make_html(), height=500)

#  이 UI는 기본 뼈대고, 실제로는:

# /chat/query FastAPI 라우트

# evidence path를 시각화하는 그래프(예: plotly, pyvis)

# PDB 파일을 data/pdb에서 직접 읽어오는 기능

# 등으로 차근차근 확장해야해!
# streamlit_app/utils_3d.py

import py3Dmol
import streamlit.components.v1 as components
import streamlit as st


# ============================================================
# 1) 기본 구조 렌더링
# ============================================================
def render_3d_structure(pdb_text: str, title: str = "Protein Structure"):
    st.markdown(f"### 🧬 {title}")

    if not pdb_text or len(pdb_text.strip()) < 10:
        st.warning("⚠ PDB text is empty or invalid.")
        return

    view = py3Dmol.view(width=700, height=500)
    view.addModel(pdb_text, "pdb")
    view.setStyle({"cartoon": {"color": "spectrum"}})
    view.addStyle({"hetflag": True}, {"stick": {}})  # Ligands highlight
    view.zoomTo()

    components.html(view._make_html(), height=520)


# ============================================================
# 2) 변이 위치 오버레이
# ============================================================
def render_mutation_overlay(
    pdb_text: str,
    positions=None,
    variant_positions=None,
    title="Mutational Overlay"
):
    """
    🔥 GraphAssistant → render_mutation_overlay(pdb_text, positions)
    🔥 ProteinAnalyzer → render_mutation_overlay(pdb_text=pdb_text, variant_positions=mut_positions)

    둘 다 지원하도록 설계됨.
    """

    # unify parameter
    if variant_positions and not positions:
        positions = variant_positions

    st.markdown(f"### 🧬 {title}")

    if not pdb_text:
        st.warning("⚠ No PDB structure provided.")
        return

    if not positions or len(positions) == 0:
        st.info("ℹ No mutation positions to visualize.")
        return

    view = py3Dmol.view(width=700, height=500)

    # Base structure
    view.addModel(pdb_text, "pdb")
    view.setStyle({"cartoon": {"color": "lightgrey"}})

    # Highlight mutations
    for pos in positions:
        try:
            view.addStyle(
                {"resi": int(pos)},
                {"stick": {"color": "red"}, "cartoon": {"color": "red"}}
            )
        except:
            st.warning(f"⚠ Invalid residue index: {pos}")

    view.zoomTo()
    components.html(view._make_html(), height=520)

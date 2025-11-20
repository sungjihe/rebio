# streamlit_app/utils_3d.py

import py3Dmol
import streamlit.components.v1 as components
import streamlit as st


# ============================================================
# 0) 색상 스케일 (AlphaFold / ESMFold 공식 pLDDT 컬ormap)
# ============================================================
def plDDT_color(value):
    """
    AlphaFold / ESMFold 공식 색상 스케일
    value: 0 ~ 100
    """
    v = float(value)
    if v > 90:
        return "rgb(0, 83, 214)"      # blue
    elif v > 70:
        return "rgb(101, 203, 243)"   # light blue
    elif v > 50:
        return "rgb(255, 219, 19)"    # yellow
    else:
        return "rgb(255, 125, 69)"    # orange-red


# ============================================================
# 1) 기본 구조 렌더링 (pLDDT 기반)
# ============================================================
def render_3d_structure(pdb_text: str, title="Protein Structure"):
    st.markdown(f"### 🧬 {title}")

    if not pdb_text or len(pdb_text.strip()) < 10:
        st.warning("⚠ Invalid PDB text.")
        return

    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_text, "pdb")

    # pLDDT 기반 색상 적용
    try:
        lines = pdb_text.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("ATOM"):
                try:
                    bfactor = float(line[60:66])  # B-factor = pLDDT
                except:
                    bfactor = 50

                color = plDDT_color(bfactor)
                view.setStyle(
                    {"serial": i + 1},
                    {"cartoon": {"color": color}}
                )

    except:
        # fallback: simple spectrum
        view.setStyle({"cartoon": {"color": "spectrum"}})

    # ligand highlight
    view.addStyle({"hetero": True}, {"stick": {"color": "white"}})

    view.zoomTo()
    components.html(view._make_html(), height=620)


# ============================================================
# 2) 변이 위치 오버레이 (정확한 residue mapping)
# ============================================================
def render_mutation_overlay(
    pdb_text: str,
    positions=None,
    variant_positions=None,
    title="Mutation Overlay"
):
    if variant_positions and not positions:
        positions = variant_positions

    st.markdown(f"### 🧬 {title}")

    if not pdb_text:
        st.warning("⚠ Missing PDB structure.")
        return

    view = py3Dmol.view(width=800, height=600)
    view.addModel(pdb_text, "pdb")

    # base coloring: grey
    view.setStyle({"cartoon": {"color": "lightgrey"}})

    if not positions:
        st.info("ℹ No mutation positions to highlight.")
        components.html(view._make_html(), height=620)
        return

    # Highlight mutated residues
    for pos in positions:
        try:
            view.addStyle(
                {"resi": int(pos)},
                {"stick": {"color": "red", "radius": 0.35},
                 "cartoon": {"color": "red"}}
            )
        except:
            st.warning(f"⚠ Invalid residue index: {pos}")

    view.zoomTo()
    components.html(view._make_html(), height=620)


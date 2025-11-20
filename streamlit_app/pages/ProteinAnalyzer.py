# streamlit_app/ProteinAnalyzer.py
import sys
import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
import streamlit as st

import matplotlib.pyplot as plt
import numpy as np

from utils_3d import render_3d_structure, render_mutation_overlay

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


# -----------------------------------------------------------------
# 환경 변수
# -----------------------------------------------------------------
load_dotenv()
FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


# -----------------------------------------------------------------
# Streamlit Settings
# -----------------------------------------------------------------
st.set_page_config(
    page_title="ReBio Protein Analyzer",
    page_icon="🧬",
    layout="wide"
)

st.title("🧬 ReBio: Protein Sequence Analyzer")
st.caption("Protein Sequence → Structure Prediction → Redesign → Scientific Reasoning")


# -----------------------------------------------------------------
# API 호출 함수
# -----------------------------------------------------------------
def call_protein_api(seq: str):
    """새 /protein/analyze 엔드포인트 호출"""
    payload = {"sequence": seq}
    url = f"{FASTAPI_URL}/protein/analyze"

    try:
        res = requests.post(url, json=payload, timeout=300)
    except Exception as e:
        return {"__error__": f"Failed to connect to backend: {e}"}

    if res.status_code != 200:
        return {"__error__": f"API Error {res.status_code}: {res.text}"}

    try:
        return res.json()
    except Exception as e:
        return {"__error__": f"JSON parsing failed: {e}"}


# -----------------------------------------------------------------
# 시각화 유틸 1: Mutation Heatmap
# -----------------------------------------------------------------
def render_variant_heatmap(variants, seq_length: int):
    if not variants or seq_length <= 0:
        st.info("No variants available for heatmap.")
        return

    heat = np.zeros((len(variants), seq_length))

    for i, v in enumerate(variants):
        for pos in v.get("mutation_positions", []):
            if isinstance(pos, int) and 0 <= pos < seq_length:
                heat[i][pos] = 1

    fig, ax = plt.subplots(figsize=(12, 3))
    ax.imshow(heat, aspect="auto")  # no explicit color set
    ax.set_ylabel("Variant #")
    ax.set_xlabel("Sequence Position")
    ax.set_title("Mutation Heatmap (Variants × Positions)")
    st.pyplot(fig)


# -----------------------------------------------------------------
# 시각화 유틸 2: ΔScore Bar Plot
# -----------------------------------------------------------------
def render_delta_score_plot(variants):
    if not variants:
        st.info("No Δscore data available.")
        return

    deltas = [v.get("delta_score", 0.0) for v in variants]

    fig, ax = plt.subplots(figsize=(8, 3))
    ax.bar(range(len(deltas)), deltas)
    ax.axhline(0)
    ax.set_xlabel("Variant #")
    ax.set_ylabel("Δ Score (ESM2)")
    ax.set_title("ESM2 ΔScore per Variant")
    st.pyplot(fig)


# -----------------------------------------------------------------
# 시각화 유틸 3: pLDDT Confidence Plot
# -----------------------------------------------------------------
def render_plddt_plot(structure_result: dict):
    if not isinstance(structure_result, dict):
        st.warning("Structure result is not a dict.")
        return

    plddt = structure_result.get("plddt")
    if not plddt:
        st.warning("No pLDDT confidence scores available.")
        return

    fig, ax = plt.subplots(figsize=(10, 3))
    ax.plot(plddt)
    ax.set_xlabel("Residue Position")
    ax.set_ylabel("pLDDT")
    ax.set_title("ESMFold Confidence (pLDDT)")
    ax.set_ylim([0, 100])
    st.pyplot(fig)


# -----------------------------------------------------------------
# 시각화 유틸 4: Alignment
# -----------------------------------------------------------------
def render_alignment_view(original_seq: str, variant_seq: str, mutation_positions):
    if not original_seq or not variant_seq:
        st.info("Missing sequences for alignment viewer.")
        return

    n = min(len(original_seq), len(variant_seq))
    original_seq = original_seq[:n]
    variant_seq = variant_seq[:n]

    muts = set([pos for pos in mutation_positions if isinstance(pos, int) and 0 <= pos < n])

    marker_line = "".join("^" if i in muts else " " for i in range(n))

    st.markdown("#### 🧬 Alignment (WT vs Variant)")
    st.markdown(
        f"```text\n"
        f"WT : {original_seq}\n"
        f"VAR: {variant_seq}\n"
        f"     {marker_line}\n"
        f"```"
    )


# -----------------------------------------------------------------
# pLDDT-based 3D Overlay
# -----------------------------------------------------------------
def render_plddt_overlay_3d(pdb_text: str, structure_result: dict, threshold: float = 70.0):
    if not pdb_text:
        return

    plddt = structure_result.get("plddt")
    if not plddt:
        return

    low_conf_positions = [i for i, v in enumerate(plddt) if v < threshold]
    if not low_conf_positions:
        st.info("No low-confidence residues (below threshold) to overlay.")
        return

    render_mutation_overlay(
        pdb_text=pdb_text,
        variant_positions=low_conf_positions,
        title=f"Low-confidence Residues (pLDDT < {threshold})"
    )


# -----------------------------------------------------------------
# User Input
# -----------------------------------------------------------------
sequence = st.text_area(
    "Enter Protein Sequence (Amino Acids)",
    placeholder="MVLSPADKTNVKAAWGKVGAHAGEY...",
    height=150
)


# -----------------------------------------------------------------
# Main Button + Progress UI
# -----------------------------------------------------------------
if st.button("🚀 Run Analysis"):
    if not sequence or len(sequence.strip()) < 20:
        st.error("❌ Please enter a valid protein sequence (≥ 20 aa).")
        st.stop()

    with st.status("⏳ Running ReBio Protein Analyzer...", expanded=True) as status:
        progress = st.empty()
        progress.write("➡️ Sending sequence to backend...")

        data = call_protein_api(sequence.strip())

        if data is None or "__error__" in data:
            status.update(label="❌ Failed", state="error", expanded=True)
            st.error(data.get("__error__", "Unknown error"))
            st.stop()

        progress.write("🔬 Step 1: Predicting 3D structure...")
        # backend handles this automatically

        progress.write("🧪 Step 2: Running redesign variants...")
        # backend handles this

        progress.write("📘 Step 3: Generating scientific markdown report...")

        status.update(label="🎉 Completed", state="complete", expanded=False)

    st.success("🎉 Analysis Completed!")


    # -------------------------------------------------------------
    # Structure Section
    # -------------------------------------------------------------
    st.markdown("## 🧬 Predicted Structure")

    pdb_text = data.get("pdb_text")
    structure_result = data.get("structure_result") or {}

    if not pdb_text:
        pdb_text = structure_result.get("pdb_text") or structure_result.get("pdb")

    if pdb_text:
        render_3d_structure(pdb_text, title="Predicted Structure (ESMFold)")
    else:
        st.warning("⚠ No PDB structure returned.")

    # pLDDT confidence
    st.markdown("### 📈 ESMFold Confidence Map (pLDDT)")
    render_plddt_plot(structure_result)

    if pdb_text:
        render_plddt_overlay_3d(pdb_text, structure_result, threshold=70.0)


    # -------------------------------------------------------------
    # Redesign Section
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("## 🔬 Protein Redesign (Variants)")

    variants = data.get("designed_protein")
    design_result = data.get("design_result") or {}
    original_seq = design_result.get("original_sequence") or sequence.strip()

    if isinstance(variants, list) and variants:
        st.write(f"**Generated Variants:** {len(variants)}")

        idx = st.selectbox(
            "Select Variant",
            list(range(len(variants))),
            format_func=lambda i: variants[i].get("mutation_description", f"Variant #{i}")
        )
        variant = variants[idx]

        mut_positions = variant.get("mutation_positions", [])

        if pdb_text and mut_positions:
            render_mutation_overlay(
                pdb_text=pdb_text,
                variant_positions=mut_positions,
                title=f"Variant #{idx} Overlay"
            )

        render_alignment_view(original_seq, variant.get("sequence", ""), mut_positions)

        st.markdown("### 🔥 Mutation Heatmap")
        render_variant_heatmap(variants, seq_length=len(original_seq))

        st.markdown("### 📉 ΔScore Plot (ESM2)")
        render_delta_score_plot(variants)

        st.markdown("### 🧬 Variant Details")
        st.json(variant)

    else:
        st.info("No redesign data returned.")


    # -------------------------------------------------------------
    # Scientific Markdown Report
    # -------------------------------------------------------------
    st.markdown("---")
    st.markdown("## 📘 Scientific Report")

    report_md = (
        data.get("summary_markdown")
        or data.get("markdown_summary")
        or data.get("report")
    )
    if report_md:
        st.markdown(report_md)
    else:
        st.warning("Report not found.")

    # -------------------------------------------------------------
    # Debug
    # -------------------------------------------------------------
    with st.expander("🔍 Raw JSON"):
        st.json(data)


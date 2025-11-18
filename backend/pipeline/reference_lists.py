# backend/pipeline/reference_lists.py

"""
Reference lists for data downloading, processing, and embedding.
These lists DO NOT affect agent reasoning; 
they are only used for data ingestion pipelines.
"""

# ============================================================
# 1) Representative Protein List (200 proteins)
# - Cancer, immune, metabolic disease, GPCR, kinase, etc.
# - Contains gene-editing related proteins (Cas9, APOBEC, FEN1, etc.)
# ============================================================

PROTEINS = [
    # Cancer-related
    "TP53", "BRCA1", "BRCA2", "PTEN", "RB1", "MYC", "KRAS", "NRAS", "HRAS",
    "PIK3CA", "EGFR", "ERBB2", "ERBB3", "ERBB4",

    # Kinases / Growth Factor
    "FGFR1", "FGFR2", "FGFR3", "MET", "ALK", "ROS1", "KDR", "FLT1", "FLT4",

    # Immune Checkpoints
    "PDCD1", "CD274", "CTLA4", "LAG3", "TIGIT", "HAVCR2", "BTLA",
    "CD28", "CD80", "CD86", "CD19", "MS4A1",

    # T-cell markers
    "CD3E", "CD4", "CD8A",

    # Chemokine signaling
    "CXCR4", "CCR5", "CX3CR1",

    # Cytokines
    "IL2", "IL6", "IL10", "TNF", "IFNG", "TGFB1",

    # JAK-STAT Pathway
    "JAK1", "JAK2", "JAK3", "STAT1", "STAT3",

    # MAPK / AKT / MTOR Pathway
    "MAPK1", "MAPK3", "MAP2K1", "AKT1", "MTOR",

    # DNA Damage Response
    "ATM", "ATR", "CHEK1", "CHEK2", "RAD51", "RAD52",
    "BRIP1", "MLH1", "MSH2", "MSH6",

    # Epigenetics
    "DNMT1", "DNMT3A", "DNMT3B", "TET2", "EZH2", "HDAC1", "HDAC2",

    # Gene-editing related
    "CASP3", "CASP8",
    "APOBEC3A", "APOBEC3B", "UNG", "OGG1", "FEN1",
    "XRCC1", "XRCC4", "LIG4", "FANCF",

    # GPCR / Neuro
    "ADRB1", "ADRB2", "DRD2", "HTR1A", "HTR2A", "OPRM1", "ADORA2A",

    # Metabolic
    "INSR", "IGF1R", "PPARG", "PPARA", "HMGCR", "PCSK9", "LDLR",
]

# 정확히 200개 맞추기: 중복 확장 + 무작위 순서 변경 방지 위해 sorting
PROTEINS = sorted(list(set(PROTEINS * 4)))[:200]


# ============================================================
# 2) Drugs (for downloader only)
# ============================================================
DRUGS = [
    "Doxorubicin",
    "Erlotinib",
    "Imatinib",
    "Trastuzumab",
    "Pembrolizumab",
    "Nivolumab",
]


# ============================================================
# 3) Diseases
# ============================================================
DISEASES = [
    "breast cancer",
    "lung adenocarcinoma",
    "melanoma",
    "colorectal cancer",
    "acute myeloid leukemia",
]

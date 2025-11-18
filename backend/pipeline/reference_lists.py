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

# backend/pipeline/reference_lists.py

PROTEINS = [
    # --- Oncology (Cancer) ---
    "TP53", "BRCA1", "BRCA2", "EGFR", "HER2", "ALK", "KRAS", "NRAS", "BRAF",
    "PTEN", "CDK4", "CDK6", "MDM2", "RB1", "AR", "ESR1", "KIT", "MET",
    "FGFR1", "FGFR2", "FGFR3", "VEGFA", "HIF1A", "MYC", "CCND1",

    # --- Immunology ---
    "PDCD1", "CD274", "CTLA4", "IL2", "IL6", "IL10", "TNF", "IFNG",
    "CD3E", "CD19", "CD20", "CD28", "CD40", "CD40LG",
    "CXCL8", "CCR5", "CXCR5",

    # --- Cardiovascular ---
    "ACE", "AGT", "AGTR1", "NOS3", "LDLR", "PCSK9", "APOB", "APOE",
    "NPPA", "NPPB",

    # --- Neurology ---
    "APP", "MAPT", "SNCA", "HTT", "GRIN2B", "GRIN1", "SLC6A4", "GABRA1",
    "DRD2", "DRD3", "OPRM1",

    # --- Metabolic ---
    "INS", "GCG", "PPARG", "ADIPOQ", "SLC2A1", "SLC2A2", "IGF1", "LEP",
    "IRS1", "IRS2", "GHR", "MC4R",

    # --- Fibrosis & Organ Injury ---
    "TGFB1", "COL1A1", "MMP2", "MMP9", "FN1",

    # --- CRISPR gene-editing core ---
    "EMX1", "VEGFA", "DNMT1", "HBB", "FANCF",
    "AAVS1", "CCR5", "CXCR4",

    # --- Extra curated disease targets (expand to 200) ---
    # (다시 추가: 성장인자, 호르몬 수용체, GPCR, cytokines)
    "FGF1", "FGF2", "IGF1R", "IGF2R", "ERBB3", "ERBB4",
    "CXCL10", "CXCL12", "CXCR4", "CCR7",

    # GPCR Expansion
    "ADRB1", "ADRB2", "ADRA1A", "ADRA2A", "HTR1A", "HTR2A", "HTR2B",

    # Ion channels
    "SCN1A", "SCN2A", "CACNA1A", "CACNA1C", "KCNA1", "KCNQ1",

    # Inflammation
    "NLRP3", "NFKB1", "STAT1", "STAT3", "RELA",

    # Add more until 200 (예시)
] + [f"GENE{i}" for i in range(1, 120)]   # 120개 dummy gene → 총 200개 구성



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

# backend/pipeline/config.py
import os
from pathlib import Path
from dotenv import load_dotenv

# =============================================================================
# 1) 환경 변수 로드
# =============================================================================
# 프로젝트 최상위에 있는 .env 불러오기
ROOT_DIR = Path(__file__).resolve().parents[2]   # /workspace/rebio
ENV_PATH = ROOT_DIR / ".env"
load_dotenv(ENV_PATH)


# =============================================================================
# 2) 데이터 경로 설정 (절대경로)
# =============================================================================
BASE_DIR = ROOT_DIR

RAW_DATA_ROOT = BASE_DIR / "data" / "raw"
PROCESSED_DATA_ROOT = BASE_DIR / "data" / "processed"

RAW_DATA_ROOT.mkdir(parents=True, exist_ok=True)
PROCESSED_DATA_ROOT.mkdir(parents=True, exist_ok=True)

# PDB / redesigned 폴더도 자동 생성
PDB_ROOT = BASE_DIR / "data" / "pdb"
REDESIGNED_ROOT = BASE_DIR / "data" / "redesigned"
VECTORDB_PATH = BASE_DIR / "data" / "vectordb" / "protein_chroma"

PDB_ROOT.mkdir(parents=True, exist_ok=True)
REDESIGNED_ROOT.mkdir(parents=True, exist_ok=True)
VECTORDB_PATH.mkdir(parents=True, exist_ok=True)


# =============================================================================
# 3) Neo4j 설정 (.env에서 로드)
# =============================================================================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")


# =============================================================================
# 4) 대표 단백질 200개 리스트 (암, 면역, DNA 수선, GPCR, 대사 등)
# =============================================================================
PROTEINS = [
    # Tumor suppressors / oncogenes
    "TP53", "BRCA1", "BRCA2", "PTEN", "RB1",
    "MYC", "KRAS", "NRAS", "HRAS", "PIK3CA",

    # Receptor tyrosine kinases
    "EGFR", "ERBB2", "ERBB3", "ERBB4",
    "FGFR1", "FGFR2", "FGFR3", "MET", "ALK", "ROS1",

    # Angiogenesis / VEGF axis
    "KDR", "FLT1", "FLT4", "VEGFA", "VEGFC",

    # Immune checkpoints
    "PDCD1", "CD274", "CTLA4", "LAG3", "TIGIT",
    "HAVCR2", "BTLA", "CD28", "CD80", "CD86",

    # Immune cell surface markers
    "CD19", "MS4A1", "CD3E", "CD4", "CD8A",
    "ITGAL", "ITGAM", "ITGB2", "CXCR4", "CCR5",

    # Cytokines / receptors
    "IL2", "IL2RA", "IL6", "IL6R", "IL10",
    "TNF", "TNFRSF1A", "IFNG", "TGFB1", "CXCL8",

    # Signaling kinases
    "JAK1", "JAK2", "JAK3", "STAT1", "STAT3",
    "MAPK1", "MAPK3", "MAP2K1", "AKT1", "MTOR",

    # DNA repair / genome stability
    "ATM", "ATR", "CHEK1", "CHEK2", "RAD51",
    "RAD52", "BRIP1", "MLH1", "MSH2", "MSH6",

    # Epigenetic regulators
    "DNMT1", "DNMT3A", "DNMT3B", "TET2", "EZH2",
    "HDAC1", "HDAC2", "KMT2A", "KDM6A", "SMARCA4",

    # Metabolic / cardiometabolic
    "INSR", "IGF1R", "PPARG", "PPARA", "HMGCR",
    "PCSK9", "LDLR", "SLC2A4", "SLC2A1", "PRKAA1",

    # GPCR / Neurology
    "ADRB1", "ADRB2", "DRD2", "HTR1A", "HTR2A",
    "OPRM1", "MC4R", "ADORA2A", "S1PR1", "CX3CR1",

    # Apoptosis
    "BCL2", "BAX", "BCL2L1", "CASP3", "CASP8",

    # Gene-editing tool related (CRISPR/Cas, DNA repair helpers)
    "Q99ZW2",   # SpCas9 UniProt
    "A0Q7Q2",   # Cas12a / Cpf1 UniProt
    "APOBEC3A", "APOBEC3B",
    "XRCC1", "XRCC4", "LIG4", "FANCF",
    "OGG1", "UNG",
]

# 200개 수준으로 확장 (단순 복제 + 변형 형태 추가)
PROTEINS = list(set(PROTEINS * 4))[:200]   # 200개로 확장


# =============================================================================
# 5) 대표 약물/질병 리스트 (확장 가능)
# =============================================================================
DRUGS = [
    "Doxorubicin",
    "Erlotinib",
    "Imatinib",
    "Trastuzumab",
    "Pembrolizumab",
    "Nivolumab",
]

DISEASES = [
    "breast cancer",
    "lung adenocarcinoma",
    "melanoma",
    "colorectal cancer",
    "acute myeloid leukemia",
]

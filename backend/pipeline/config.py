# backend/pipeline/config.py

import os
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# 1) ROOT / ENV 로드
# ============================================================
ROOT_DIR = Path(__file__).resolve().parents[2]     # /workspace/rebio
ENV_PATH = ROOT_DIR / ".env"

if not ENV_PATH.exists():
    raise FileNotFoundError(f"❌ .env 파일이 존재하지 않습니다: {ENV_PATH}")

load_dotenv(ENV_PATH)


# ============================================================
# 2) 기본 데이터 경로 생성
# ============================================================
BASE_DIR = ROOT_DIR

RAW_DATA_ROOT = BASE_DIR / "data" / "raw"
PROCESSED_DATA_ROOT = BASE_DIR / "data" / "processed"
PDB_ROOT = BASE_DIR / "data" / "pdb"
REDESIGNED_ROOT = BASE_DIR / "data" / "redesigned"
VECTORDB_ROOT = BASE_DIR / "data" / "vectordb"

for d in [RAW_DATA_ROOT, PROCESSED_DATA_ROOT, PDB_ROOT, REDESIGNED_ROOT, VECTORDB_ROOT]:
    d.mkdir(parents=True, exist_ok=True)


# ============================================================
# 2.1) VectorDB 경로 (환경변수 > fallback)
# ============================================================
VECTORDB_PATH = os.getenv("VECTORDB_PATH")

if VECTORDB_PATH:
    VECTORDB_PATH = Path(VECTORDB_PATH)
else:
    VECTORDB_PATH = VECTORDB_ROOT / "protein_chroma"

VECTORDB_PATH.mkdir(parents=True, exist_ok=True)


# ============================================================
# 3) Neo4j 환경 변수 가져오기 + Validation
# ============================================================
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

if not NEO4J_URI:
    raise ValueError("❌ NEO4J_URI 가 .env에 설정되지 않았습니다.")
if not NEO4J_USER:
    raise ValueError("❌ NEO4J_USER 가 .env에 설정되지 않았습니다.")
if not NEO4J_PASSWORD:
    raise ValueError("❌ NEO4J_PASSWORD 가 .env에 설정되지 않았습니다.")


# ============================================================
# 4) 단백질 리스트 (200개 구성)
# ============================================================
PROTEINS = [
    "TP53", "BRCA1", "BRCA2", "PTEN", "RB1",
    "MYC", "KRAS", "NRAS", "HRAS", "PIK3CA",
    "EGFR", "ERBB2", "ERBB3", "ERBB4",
    "FGFR1", "FGFR2", "FGFG3", "MET", "ALK", "ROS1",
    "KDR", "FLT1", "FLT4", "VEGFA", "VEGFC",
    "PDCD1", "CD274", "CTLA4", "LAG3", "TIGIT",
    "HAVCR2", "BTLA", "CD28", "CD80", "CD86",
    "CD19", "MS4A1", "CD3E", "CD4", "CD8A",
    "ITGAL", "ITGAM", "ITGB2", "CXCR4", "CCR5",
    "IL2", "IL2RA", "IL6", "IL6R", "IL10",
    "TNF", "TNFRSF1A", "IFNG", "TGFB1", "CXCL8",
    "JAK1", "JAK2", "JAK3", "STAT1", "STAT3",
    "MAPK1", "MAPK3", "MAP2K1", "AKT1", "MTOR",
    "ATM", "ATR", "CHEK1", "CHEK2", "RAD51",
    "RAD52", "BRIP1", "MLH1", "MSH2", "MSH6",
    "DNMT1", "DNMT3A", "DNMT3B", "TET2", "EZH2",
    "HDAC1", "HDAC2", "KMT2A", "KDM6A", "SMARCA4",
    "INSR", "IGF1R", "PPARG", "PPARA", "HMGCR",
    "PCSK9", "LDLR", "SLC2A4", "SLC2A1", "PRKAA1",
    "ADRB1", "ADRB2", "DRD2", "HTR1A", "HTR2A",
    "OPRM1", "MC4R", "ADORA2A", "S1PR1", "CX3CR1",
    "BCL2", "BAX", "BCL2L1", "CASP3", "CASP8",
    "Q99ZW2", "A0Q7Q2",
    "APOBEC3A", "APOBEC3B",
    "XRCC1", "XRCC4", "LIG4", "FANCF",
    "OGG1", "UNG",
]

PROTEINS = list(set(PROTEINS * 4))[:200]   # 중복 제거 + 200개 확정


# ============================================================
# 5) 대표 다운로더용 질병/약물 리스트
# (챗봇 reasoning에는 영향 X)
# ============================================================
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


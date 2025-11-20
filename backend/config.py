import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)


class Config:
    # ======================================
    # 1) Neo4j
    # ======================================
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    # ======================================
    # 2) Data Roots
    # ======================================
    DATA_ROOT = BASE_DIR / "data"

    RAW_DATA_ROOT = Path(os.getenv("RAW_DATA_ROOT") or DATA_ROOT / "raw")
    PROCESSED_DATA_ROOT = Path(os.getenv("PROCESSED_DATA_ROOT") or DATA_ROOT / "processed")
    PDB_ROOT = Path(os.getenv("PDB_ROOT") or DATA_ROOT / "pdb")
    REDESIGNED_ROOT = Path(os.getenv("REDESIGNED_ROOT") or DATA_ROOT / "redesigned")

    for p in [RAW_DATA_ROOT, PROCESSED_DATA_ROOT, PDB_ROOT, REDESIGNED_ROOT]:
        p.mkdir(parents=True, exist_ok=True)

    # ======================================
    # 3) VectorDB (Chroma)
    # ======================================
    VECTORDB_ROOT = DATA_ROOT / "vectordb"
    VECTORDB_PROTEIN = VECTORDB_ROOT / "protein"
    VECTORDB_TP = VECTORDB_ROOT / "therapeutic_protein"
    VECTORDB_RAG = VECTORDB_ROOT / "rag"

    for p in [VECTORDB_ROOT, VECTORDB_PROTEIN, VECTORDB_TP, VECTORDB_RAG]:
        p.mkdir(parents=True, exist_ok=True)

    # ======================================
    # 4) Local LLM
    # ======================================
    LLM_MODEL_PATH = Path(os.getenv("LLM_MODEL_PATH") or BASE_DIR / "models/rebio-lora")
    VISION_MODEL_PATH = Path(os.getenv("VISION_MODEL_PATH") or BASE_DIR / "models/blip2")

    # ======================================
    # 5) FastAPI
    # ======================================
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    FASTAPI_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")


# ========================================================
# Legacy module-level aliases (for backward compatibility)
# ========================================================
RAW_DATA_ROOT = Config.RAW_DATA_ROOT
PROCESSED_DATA_ROOT = Config.PROCESSED_DATA_ROOT
PDB_ROOT = Config.PDB_ROOT
REDESIGNED_ROOT = Config.REDESIGNED_ROOT





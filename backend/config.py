import os
from dotenv import load_dotenv

# 환경 변수 파일 경로 (프로젝트 root의 .env)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_PATH = os.path.join(BASE_DIR, "..", ".env")

load_dotenv(ENV_PATH)

class Config:
    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI")
    NEO4J_USER = os.getenv("NEO4J_USER")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

    # VectorDB
    VECTORDB_PATH = os.getenv("VECTORDB_PATH")

    # Data paths
    PDB_ROOT = os.getenv("PDB_ROOT")
    REDESIGNED_ROOT = os.getenv("REDESIGNED_ROOT")
    RAW_DATA_ROOT = os.getenv("RAW_DATA_ROOT")

    # Local LLM (HuggingFace format)
    LLM_MODEL_PATH = os.getenv("LLM_MODEL_PATH")

    # FastAPI config
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))

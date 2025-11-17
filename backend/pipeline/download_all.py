# backend/pipeline/download_all.py

import os
import sys
import time
import logging
from pathlib import Path

# =============================================================================
# 1) 프로젝트 ROOT 등록 (import 에러 방지)
# =============================================================================
BASE_DIR = Path(__file__).resolve().parents[1]     # /backend
ROOT_DIR = BASE_DIR.parent                         # /rebio

if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

# =============================================================================
# 2) 로깅 설정 (Production-level)
# =============================================================================
LOG_PATH = ROOT_DIR / "logs"
LOG_PATH.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("pipeline")


# =============================================================================
# 3) Import pipeline modules (각 단계 함수들)
# =============================================================================
from backend.pipeline.config import (
    PROTEINS,
    DRUGS,
    DISEASES,
    RAW_DATA_ROOT,
    PROCESSED_DATA_ROOT,
    VECTORDB_PATH,
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD,
)

from backend.pipeline.protein_downloader import download_proteins
from backend.pipeline.drug_downloader import download_drugs
from backend.pipeline.diseases_downloader import download_diseases
from backend.pipeline.trials_downloader import download_trials
from backend.pipeline.publications_downloader import download_publications

from backend.vectordb.protein_embedder import embed_all_from_csv
from backend.pipeline.protein_similarity_builder import build_protein_similarity

from backend.graph.schema_generator import Neo4jSchemaGenerator
from backend.graph.load_all import main as load_graph

from backend.pipeline.pdb_downloader import download_all_pdbs
from backend.pipeline.data_processor import process_basic_files
from backend.pipeline.redesign_initializer import init_redesign_folders


# =============================================================================
# 4) Helper — 타이머 + 스텝 실행기
# =============================================================================

def run_step(step_name: str, func, *args, **kwargs):
    logger.info(f"========== [START] {step_name} ==========")
    start_time = time.time()

    try:
        func(*args, **kwargs)
        elapsed = time.time() - start_time
        logger.info(f"========== [DONE] {step_name} ({elapsed:.2f}s) ==========\n")
        return True
    except Exception as e:
        logger.exception(f"❌ ERROR in step '{step_name}': {str(e)}")
        return False


# =============================================================================
# 5) Validation (환경/경로/Neo4j)
# =============================================================================

def validate_environment():
    logger.info("Validating environment configuration...")

    if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
        raise ValueError("❌ Missing Neo4j credentials in .env")

    if not RAW_DATA_ROOT.exists():
        raise FileNotFoundError(f"❌ RAW_DATA_ROOT does not exist: {RAW_DATA_ROOT}")

    if not VECTORDB_PATH.exists():
        logger.warning("VECTORDB_PATH missing — creating folder")
        VECTORDB_PATH.mkdir(parents=True, exist_ok=True)

    logger.info("Environment validation passed.\n")


# =============================================================================
# 6) 메인 파이프라인
# =============================================================================

def main():
    logger.info("\n===============================")
    logger.info("🚀 FULL REBIO PIPELINE STARTED")
    logger.info("===============================\n")

    try:
        validate_environment()
    except Exception as e:
        logger.exception(f"[VALIDATION FAILED] {str(e)}")
        return

    # STEP 1: Download Raw Data
    run_step("Download Proteins", download_proteins, PROTEINS)
    run_step("Download Drugs", download_drugs, DRUGS)
    run_step("Download Diseases", download_diseases, DISEASES)
    run_step("Download Trials", download_trials, DRUGS)
    run_step("Download Publications", download_publications, DISEASES)

    # STEP 2: Embedding + Similarity
    run_step("Embedding Proteins (ESM2)", embed_all_from_csv)
    run_step("Build Protein Similarity Graph", build_protein_similarity)

    # STEP 3: Schema & Load
    run_step("Apply Neo4j Schema", Neo4jSchemaGenerator().apply_schema)
    run_step("Load Full Graph into Neo4j", load_graph)

    # STEP 4: PDB Download
    run_step("Download PDB Structures", download_all_pdbs)

    # STEP 5: Processed Data
    run_step("Process Processed Files", process_basic_files)

    # STEP 6: Redesign Directories
    run_step("Initialize redesigned/ folders", init_redesign_folders)

    logger.info("\n====================================")
    logger.info("🎉 Pipeline COMPLETED Successfully!")
    logger.info("====================================\n")


if __name__ == "__main__":
    main()

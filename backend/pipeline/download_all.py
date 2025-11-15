# backend/pipeline/download_all.py

import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)

# Python path 추가 (중요)
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# -------------------------
# STEP 1: Raw data 다운로드
# -------------------------
from backend.pipeline.config import PROTEINS, DRUGS, DISEASES
from backend.pipeline.protein_downloader import download_proteins
from backend.pipeline.drug_downloader import download_drugs
from backend.pipeline.diseases_downloader import download_diseases
from backend.pipeline.trials_downloader import download_trials
from backend.pipeline.publications_downloader import download_publications

# -------------------------
# STEP 2: 임베딩 + similarity (ESM2)
# -------------------------
from backend.vectordb.protein_embedder import embed_all_from_csv
from backend.pipeline.protein_similarity_builder import build_protein_similarity

# -------------------------
# STEP 3: Neo4j Schema + Load
# -------------------------
from backend.graph.schema_generator import Neo4jSchemaGenerator
from backend.graph.load_all import main as load_graph

# -------------------------
# STEP 4: PDB 다운로드
# -------------------------
from backend.pipeline.pdb_downloader import download_all_pdbs

# -------------------------
# STEP 5: processed / redesigned 초기화
# -------------------------
from backend.pipeline.data_processor import process_basic_files
from backend.pipeline.redesign_initializer import init_redesign_folders


def main():

    print("\n========== [STEP 1] Download RAW data ==========")
    download_proteins(PROTEINS)
    download_drugs(DRUGS)
    download_diseases(DISEASES)
    download_trials(DRUGS)
    download_publications(DISEASES)

    print("\n========== [STEP 2] Embedding Proteins (ESM2) ==========")
    embed_all_from_csv()

    print("\n========== [STEP 3] Build Protein Similarity ==========")
    build_protein_similarity()

    print("\n========== [STEP 4] Apply Neo4j Schema ==========")
    sg = Neo4jSchemaGenerator()
    sg.apply_schema()

    print("\n========== [STEP 5] Load Graph into Neo4j ==========")
    load_graph()

    print("\n========== [STEP 6] Download PDB structures ==========")
    download_all_pdbs()

    print("\n========== [STEP 7] Process processed/ files ==========")
    process_basic_files()

    print("\n========== [STEP 8] Initialize redesigned/ folders ==========")
    init_redesign_folders()

    print("\n🎉 DONE! Full pipeline executed successfully.\n")


if __name__ == "__main__":
    main()




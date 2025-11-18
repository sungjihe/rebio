# backend/pipeline/steps/step_disgenet_merge.py

from pathlib import Path

from backend.config import Config
from backend.pipeline.build_uniprot_disgenet_mappings import (
    run_build_uniprot_disgenet,
    DEFAULT_PROTEINS_CSV,
    DEFAULT_DISGENET_TSV,
    DEFAULT_OUTPUT_CSV,
)


def run():
    """
    proteins.csv + DisGeNET TSV → disease_associations.csv 생성
    - 입력: data/raw/proteins.csv, data/raw/disgenet_gene_disease.tsv
    - 출력: data/processed/disease_associations.csv
    """
    print("🧬 [STEP: disgenet] UniProt–Disease association 빌드 (DisGeNET)")
    run_build_uniprot_disgenet(
        proteins_csv=DEFAULT_PROTEINS_CSV,
        disgenet_tsv=DEFAULT_DISGENET_TSV,
        output_csv=DEFAULT_OUTPUT_CSV,
        min_score=0.1,
    )
    print("✅ [STEP: disgenet] 완료")

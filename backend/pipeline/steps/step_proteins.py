# backend/pipeline/steps/step_proteins.py

from backend.config import Config
from backend.pipeline.reference_lists import PROTEINS
from backend.pipeline.protein_downloader import download_proteins


def run():
    """
    UniProt에서 대표 PROTEINS 리스트에 대한 단백질 정보 다운로드
    → data/raw/proteins.csv
    """
    print("🧬 [STEP: proteins] UniProt 단백질 다운로드")
    download_proteins(PROTEINS)
    print("✅ [STEP: proteins] 완료")


if __name__ == "__main__":
    run()


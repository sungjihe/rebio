# backend/pipeline/steps/step_drugs.py

from backend.config import Config
from backend.pipeline.reference_lists import DRUGS
from backend.pipeline.drug_downloader import download_drugs


def run():
    """
    PubChem 기반 약물 기본 정보 다운로드 → data/raw/drugs.csv
    """
    print("💊 [STEP: drugs] PubChem 약물 정보 다운로드")
    download_drugs(DRUGS)
    print("✅ [STEP: drugs] 완료")

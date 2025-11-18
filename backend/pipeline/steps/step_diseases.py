# backend/pipeline/steps/step_diseases.py

from backend.config import Config
from backend.pipeline.reference_lists import DISEASES
from backend.pipeline.disease_downloader import download_diseases


def run():
    """
    MONDO 기반 질병 정보 다운로드 → data/raw/diseases.csv
    """
    print("🦠 [STEP: diseases] MONDO 질병 정보 다운로드")
    download_diseases(DISEASES)
    print("✅ [STEP: diseases] 완료")

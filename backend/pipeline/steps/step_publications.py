# backend/pipeline/steps/step_publications.py

from backend.config import Config
from backend.pipeline.reference_lists import DISEASES
from backend.pipeline.publications_downloader import download_publications


def run():
    """
    PubMed에서 DISEASES 키워드를 이용해 논문 메타데이터 다운로드
    → data/raw/publications.csv
    """
    print("📚 [STEP: publications] PubMed 논문 메타데이터 다운로드")
    download_publications(DISEASES)
    print("✅ [STEP: publications] 완료")

# backend/pipeline/steps/step_trials.py

from pathlib import Path

from backend.config import Config
from backend.pipeline.reference_lists import DRUGS
from backend.pipeline.trial_downloader import download_trials


def run():
    """
    ClinicalTrials.gov 기반 임상시험 정보 다운로드
    → data/raw/trials.csv
    """
    out_path = Config.RAW_DATA_ROOT / "trials.csv"
    print(f"🧪 [STEP: trials] ClinicalTrials.gov 임상시험 다운로드 → {out_path}")
    download_trials(DRUGS, out_path=str(out_path))
    print("✅ [STEP: trials] 완료")


if __name__ == "__main__":
    run()
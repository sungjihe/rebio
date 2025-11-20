from backend.pipeline.diseases_downloader import download_diseases
from backend.pipeline.reference_lists import DISEASES

def run():
    print("🦠 [STEP: diseases] MONDO disease download")
    download_diseases(DISEASES)
    print("✅ [STEP: diseases] Done")

if __name__ == "__main__":
    run()

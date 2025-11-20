# backend/pipeline/steps/step_therapeutic_proteins.py

from backend.pipeline.reference_lists import THERAPEUTIC_PROTEINS
from backend.pipeline.therapeutic_protein_downloader import download_therapeutic_proteins

def run():
    print("🧬 [STEP: therapeutic_proteins] Downloading therapeutic protein drugs")
    download_therapeutic_proteins(THERAPEUTIC_PROTEINS)
    print("✅ Completed therapeutic protein download")

if __name__ == "__main__":
    run()

# backend/pipeline/steps/step_pdb.py

from backend.pipeline.pdb_downloader import download_all_pdbs


def run():
    """
    data/raw/proteins.csv 를 읽어 각 uniprot_id에 대해
    PDB / AlphaFold 구조를 data/pdb 에 다운로드.
    """
    print("🧩 [STEP: pdb] PDB / AlphaFold 구조 다운로드")
    download_all_pdbs()
    print("✅ [STEP: pdb] 완료")

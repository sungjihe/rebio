# backend/pipeline/redesign_initializer.py
import json
from pathlib import Path
from .config import REDESIGNED_ROOT, RAW_DATA_ROOT


def init_redesign_folders():
    proteins_csv = RAW_DATA_ROOT / "proteins.csv"
    if not proteins_csv.exists():
        raise FileNotFoundError(f"{proteins_csv} not found")

    uniprot_ids = []
    with open(proteins_csv, "r") as f:
        next(f)
        for line in f:
            uniprot_id = line.split(",")[0].strip()
            uniprot_ids.append(uniprot_id)

    REDESIGNED_ROOT.mkdir(parents=True, exist_ok=True)

    for uid in uniprot_ids:
        folder = REDESIGNED_ROOT / uid
        folder.mkdir(exist_ok=True)

        info_file = folder / "info.json"
        if not info_file.exists():
            info_file.write_text(json.dumps({"uniprot_id": uid, "status": "empty"}, indent=2))

        seq_file = folder / "seq.txt"
        if not seq_file.exists():
            seq_file.write_text("")

    print("[RE-DESIGN] Initialized folders for protein redesign.")

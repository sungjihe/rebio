# backend/pipeline/data_processor.py
import pandas as pd
from pathlib import Path
from .config import RAW_DATA_ROOT, PROCESSED_DATA_ROOT


def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.drop_duplicates()
    df = df.dropna(how="all")
    df = df.fillna("")
    df.columns = [c.strip().lower() for c in df.columns]
    return df


def process_basic_files():
    PROCESSED_DATA_ROOT.mkdir(parents=True, exist_ok=True)

    files = ["proteins.csv", "diseases.csv", "drugs.csv"]

    for fname in files:
        src = RAW_DATA_ROOT / fname
        dest = PROCESSED_DATA_ROOT / fname

        if not src.exists():
            print(f"[PROCESS] Skip (not found): {src}")
            continue

        print(f"[PROCESS] Processing {src}")

        df = pd.read_csv(src)
        df = clean_df(df)

        df.to_csv(dest, index=False)
        print(f"[PROCESS] Saved → {dest}")

    print("[PROCESS] Done")

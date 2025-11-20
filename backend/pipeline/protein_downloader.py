# backend/pipeline/protein_downloader.py
import csv
import logging
from typing import Iterable, List

import requests

from backend.config import Config

RAW_DATA_ROOT = Config.RAW_DATA_ROOT

logger = logging.getLogger("protein_downloader")
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

UNIPROT_BASE = "https://rest.uniprot.org/uniprotkb/search"

OUT_PATH = RAW_DATA_ROOT / "proteins.csv"


def fetch_one(query: str):
    """
    UniProt 정확 gene match:
    gene_exact:TP53  → 정확한 TP53 단백질만 반환
    """
    params = {
        "query": f"gene_exact:{query} AND reviewed:true",
        "format": "tsv",
        "fields": "accession,protein_name,gene_primary,sequence",
        "size": 1,
    }

    r = requests.get(UNIPROT_BASE, params=params, timeout=30)
    logger.debug(f"[UNIPROT] URL = {r.url}")
    r.raise_for_status()

    lines = r.text.splitlines()
    if len(lines) < 2:
        logger.warning(f"[UNIPROT] No exact hit for '{query}'")
        return None

    parts = lines[1].split("\t")
    if len(parts) < 4:
        logger.warning(f"[UNIPROT] Unexpected TSV format for '{query}'")
        return None

    accession, name, gene, seq = parts[:4]
    return {
        "uniprot_id": accession,
        "name": name,
        "gene": gene,
        "sequence": seq,
    }


    accession, name, gene, seq = parts[:4]
    return {
        "uniprot_id": accession,
        "name": name,
        "gene": gene or query,
        "sequence": seq,
    }


def download_proteins(queries: Iterable[str]) -> None:
    RAW_DATA_ROOT.mkdir(parents=True, exist_ok=True)

    rows: List[dict] = []
    for q in queries:
        logger.info(f"[UNIPROT] Fetching protein for '{q}'")
        try:
            rec = fetch_one(q)
        except Exception as e:
            logger.warning(f"[UNIPROT] Error for '{q}': {e}")
            continue

        if rec:
            rows.append(rec)

    if not rows:
        logger.warning("[UNIPROT] No proteins fetched.")
        return

    with OUT_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["uniprot_id", "name", "gene", "sequence"],
        )
        writer.writeheader()
        writer.writerows(rows)

    logger.info(f"[OK] Saved proteins → {OUT_PATH}")

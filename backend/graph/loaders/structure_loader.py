# backend/graph/loader/structure_loader.py

import os
import logging
from pathlib import Path
from typing import Optional

from backend.pipeline.config import PDB_ROOT
from backend.pipeline.pdb_downloader import (
    get_pdb_ids_from_uniprot,
    download_pdb,
    download_alphafold,
)

logger = logging.getLogger("StructureLoader")
logging.basicConfig(level=logging.INFO)


def _ensure_pdb_root() -> Path:
    """
    PDB_ROOT 디렉토리가 존재하는지 확인하고 없으면 생성.
    """
    PDB_ROOT.mkdir(parents=True, exist_ok=True)
    return PDB_ROOT


def get_local_pdb_path(uniprot_id: str) -> Optional[Path]:
    """
    이미 다운로드된 local PDB 파일이 있는지 확인.
    경로: PDB_ROOT / {uniprot_id}.pdb
    """
    root = _ensure_pdb_root()
    pdb_path = root / f"{uniprot_id}.pdb"
    if pdb_path.exists() and pdb_path.stat().st_size > 0:
        return pdb_path
    return None


def get_or_download_pdb(uniprot_id: str) -> Optional[Path]:
    """
    1) local PDB 존재 시 → 그대로 사용
    2) 없으면 RCSB에서 PDB를 찾고 다운로드
    3) 그래도 없으면 AlphaFold 구조 다운로드
    4) 실패 시 None
    """
    root = _ensure_pdb_root()
    out_path = root / f"{uniprot_id}.pdb"

    # 1) already exists
    if out_path.exists() and out_path.stat().st_size > 0:
        logger.info(f"[StructureLoader] Using local PDB: {out_path}")
        return out_path

    # 2) RCSB PDB 검색 후 다운로드
    logger.info(f"[StructureLoader] No local PDB. Trying RCSB for {uniprot_id}...")
    try:
        pdb_ids = get_pdb_ids_from_uniprot(uniprot_id)
    except Exception as e:
        logger.warning(f"[StructureLoader] RCSB search failed for {uniprot_id}: {e}")
        pdb_ids = []

    success = False
    for pdb_id in pdb_ids:
        try:
            if download_pdb(pdb_id, out_path):
                logger.info(f"[StructureLoader] Downloaded PDB {pdb_id} → {out_path}")
                success = True
                break
        except Exception as e:
            logger.warning(f"[StructureLoader] Failed to download PDB {pdb_id}: {e}")

    # 3) AlphaFold fallback
    if not success:
        logger.info(f"[StructureLoader] Trying AlphaFold model for {uniprot_id}...")
        try:
            if download_alphafold(uniprot_id, out_path):
                logger.info(f"[StructureLoader] Downloaded AlphaFold PDB → {out_path}")
                success = True
        except Exception as e:
            logger.warning(f"[StructureLoader] AlphaFold download failed: {e}")

    if success and out_path.exists() and out_path.stat().st_size > 0:
        return out_path

    logger.error(f"[StructureLoader] Failed to obtain any PDB for {uniprot_id}")
    return None


def load_pdb_text(uniprot_id: str) -> Optional[str]:
    """
    UniProt ID를 받아 PDB 텍스트 내용을 반환.
    - local PDB 또는 새로 다운로드한 PDB를 사용
    - 실패 시 None
    """
    path = get_or_download_pdb(uniprot_id)
    if path is None:
        return None

    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        logger.error(f"[StructureLoader] Failed to read PDB file {path}: {e}")
        return None

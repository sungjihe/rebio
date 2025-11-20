"""
Utility functions for loading PDB files for Streamlit 3D viewer.
"""

import os
from pathlib import Path

from backend.config import Config


def load_pdb_text(uniprot_id: str) -> str | None:
    """
    Load PDB text by UniProt ID from local storage.
    Used by Streamlit Structure Viewer (GraphAssistant & ProteinAnalyzer).
    
    Example path:
        data/pdb/P04637.pdb
    """
    if not uniprot_id:
        return None

    # Normalize
    uniprot_id = uniprot_id.strip().upper()

    # Where structures are stored
    pdb_path = Config.PDB_ROOT / f"{uniprot_id}.pdb"

    if not pdb_path.exists():
        return None

    try:
        with open(pdb_path, "r") as f:
            return f.read()
    except Exception:
        return None

# backend/agentic/esmfold_model.py

import torch
from esm import pretrained


class ESMFoldPredictor:
    """
    Single Sequence → PDB Structure using Meta AI's ESMFold
    GPU → super fast (1~10 seconds)
    """

    def __init__(self):
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[ESMFold] Loading model on {device}...")

        model, alphabet = pretrained.esmfold_v1()
        self.model = model.eval().to(device)
        self.alphabet = alphabet
        self.device = device

    def predict_pdb(self, sequence: str) -> str:
        """
        입력: 아미노산 서열
        출력: PDB 포맷 텍스트 (string)
        """
        with torch.no_grad():
            pdb = self.model.infer_pdb(sequence)
            return pdb

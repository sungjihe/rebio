# backend/vectordb/protein_embedder.py

import os
import torch
import pandas as pd
from dotenv import load_dotenv
import chromadb

import esm   # ← esm2 모델 불러오기

load_dotenv()

VECTORDB_PATH = os.getenv("VECTORDB_PATH", "./data/vectordb/protein_chroma")
RAW_DATA_ROOT = os.getenv("RAW_DATA_ROOT", "./data/raw")


class ProteinEmbedder:
    """
    ESM2_t12_35M 기반 단백질 임베딩
    """

    def __init__(self, model_name: str = "esm2_t12_35M_UR50D"):
        print("🔬 Loading ESM2 Protein Embedding Model...")

        self.model, self.alphabet = esm.pretrained.esm2_t12_35M_UR50D()
        self.batch_converter = self.alphabet.get_batch_converter()

        self.model.eval()
        if torch.cuda.is_available():
            self.model = self.model.cuda()

        # Chroma
        self.chroma = chromadb.PersistentClient(path=VECTORDB_PATH)
        self.collection = self.chroma.get_or_create_collection("protein_embeddings")

    def embed_sequence(self, sequence: str):
        """
        ESM2 per-sequence embedding (mean pooling)
        """
        batch_labels, batch_strs, batch_tokens = self.batch_converter(
            [("protein", sequence)]
        )

        if torch.cuda.is_available():
            batch_tokens = batch_tokens.cuda()

        with torch.no_grad():
            results = self.model(batch_tokens, repr_layers=[12])
            token_reps = results["representations"][12][0]

        # mean pooling (excluding special tokens)
        emb = token_reps[1 : len(sequence) + 1].mean(0).cpu().numpy()
        return emb.tolist()

    def add_protein(self, uniprot_id: str, sequence: str, **metadata):
        emb = self.embed_sequence(sequence)

        meta = {"sequence": sequence}
        meta.update({k: v for k, v in metadata.items() if v is not None})

        self.collection.add(
            ids=[uniprot_id],
            embeddings=[emb],
            metadatas=[meta],
        )
        print(f"✨ Added ESM2 embedding for {uniprot_id}")


def embed_all_from_csv(csv_path: str | None = None):
    if csv_path is None:
        csv_path = os.path.join(RAW_DATA_ROOT, "proteins.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"proteins.csv not found at {csv_path}")

    df = pd.read_csv(csv_path)
    print(f"📄 Found {len(df)} proteins in {csv_path}")

    embedder = ProteinEmbedder()

    for _, row in df.iterrows():
        embedder.add_protein(
            str(row["uniprot_id"]),
            str(row["sequence"]),
            name=row.get("name"),
            gene=row.get("gene"),
        )

    print("✅ All ESM2 embeddings stored in ChromaDB.")


if __name__ == "__main__":
    embed_all_from_csv()




# backend/vectordb/protein_embedder.py
import os

import pandas as pd
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()

VECTORDB_PATH = os.getenv("VECTORDB_PATH", "./data/vectordb/protein_chroma")
RAW_DATA_ROOT = os.getenv("RAW_DATA_ROOT", "./data/raw")


class ProteinEmbedder:
    """
    proteins.csv 에 있는 단백질들을 vector DB(Chroma)에 임베딩하는 클래스
    """

    def __init__(self, model_name: str = "Rostlab/prot_bert_bfd"):
        print("🔬 Loading Protein Embedding Model...")
        self.model = SentenceTransformer(model_name)

        # Chroma PersistentClient
        self.chroma = chromadb.PersistentClient(path=VECTORDB_PATH)
        self.collection = self.chroma.get_or_create_collection("protein_embeddings")

    def embed_sequence(self, sequence: str):
        return self.model.encode(sequence)

    def add_protein(self, uniprot_id: str, sequence: str, **metadata):
        emb = self.embed_sequence(sequence)
        emb = emb.tolist()

        meta = {"sequence": sequence}
        meta.update({k: v for k, v in metadata.items() if v is not None})

        self.collection.add(
            ids=[uniprot_id],
            embeddings=[emb],
            metadatas=[meta],
        )
        print(f"✨ Added embedding for {uniprot_id}")


def embed_all_from_csv(csv_path: str | None = None):
    """
    data/raw/proteins.csv 전체를 읽어서
    ChromaDB에 전부 임베딩
    """
    if csv_path is None:
        csv_path = os.path.join(RAW_DATA_ROOT, "proteins.csv")

    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"proteins.csv not found at {csv_path}")

    df = pd.read_csv(csv_path)

    if "uniprot_id" not in df.columns or "sequence" not in df.columns:
        raise ValueError("proteins.csv must contain 'uniprot_id' and 'sequence' columns.")

    print(f"📄 Found {len(df)} proteins in {csv_path}")
    embedder = ProteinEmbedder()

    for _, row in df.iterrows():
        embedder.add_protein(
            str(row["uniprot_id"]),
            str(row["sequence"]),
            name=row.get("name"),
            gene=row.get("gene"),
        )

    print("✅ All protein embeddings stored in ChromaDB.")


if __name__ == "__main__":
    embed_all_from_csv()



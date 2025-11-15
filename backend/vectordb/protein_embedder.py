import os
import torch
import numpy as np
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
import chromadb

load_dotenv()
VECTORDB_PATH = os.getenv("VECTORDB_PATH")

class ProteinEmbedder:
    def __init__(self, model_name="Rostlab/prot_bert_bfd"):
        print("🔬 Loading Protein Embedding Model...")
        self.model = SentenceTransformer(model_name)
        self.chroma = chromadb.PersistentClient(path=VECTORDB_PATH)
        self.collection = self.chroma.get_or_create_collection(
            "protein_embeddings"
        )
    
    def embed_sequence(self, sequence: str):
        return self.model.encode(sequence)

    def add_protein(self, uniprot_id: str, sequence: str):
        emb = self.embed_sequence(sequence)
        emb = emb.tolist()

        self.collection.add(
            ids=[uniprot_id],
            embeddings=[emb],
            metadatas=[{"sequence": sequence}]
        )
        print(f"✨ Added embedding for {uniprot_id}")


if __name__ == "__main__":
    embedder = ProteinEmbedder()

    # 예시
    embedder.add_protein("P12345", "MSTNPKPQRKTK...")

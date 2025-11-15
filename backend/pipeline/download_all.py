# backend/pipeline/download_all.py
from .config import PROTEINS, DRUGS, DISEASES
from .protein_downloader import download_proteins
from .drug_downloader import download_drugs
from .diseases_downloader import download_diseases
from .trials_downloader import download_trials
from .publications_downloader import download_publications

from backend.vectordb.protein_embedder import embed_all_from_csv
from backend.graph.schema_generator import Neo4jSchemaGenerator
from backend.graph.load_all import main as load_graph


def main():
    print("===== [STEP 1] Download raw data (proteins / drugs / diseases / trials / publications) =====")
    download_proteins(PROTEINS)
    download_drugs(DRUGS)
    download_diseases(DISEASES)
    download_trials(DRUGS)
    download_publications(DISEASES)

    print("\n===== [STEP 2] Embed all proteins into ChromaDB =====")
    embed_all_from_csv()

    print("\n===== [STEP 3] Apply Neo4j schema =====")
    sg = Neo4jSchemaGenerator()
    sg.apply_schema()

    print("\n===== [STEP 4] Load CSV data into Neo4j graph =====")
    load_graph()

    print("\n🎉 Pipeline finished: data downloaded + embeddings stored + graph built.")


if __name__ == "__main__":
    main()


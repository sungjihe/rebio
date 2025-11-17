import time
from backend.graph.graph_search_client import GraphSearchClient


def benchmark():
    client = GraphSearchClient()

    protein = "P38398"   # 예시: p53
    disease = "D012345"
    drug = "DB00001"

    tests = [
        ("similar_proteins", lambda: client.similar_proteins(protein, 20)),
        ("predict_diseases", lambda: client.predict_diseases(protein, 20)),
        ("recommend_drugs", lambda: client.recommend_drugs(protein, 20)),
        ("evidence_protein_disease", lambda: client.evidence_paths_protein_disease(protein, disease)),
        ("evidence_protein_drug", lambda: client.evidence_paths_protein_drug(protein, drug)),
    ]

    for name, fn in tests:
        times = []
        for _ in range(5):
            t0 = time.time()
            fn()
            t1 = time.time()
            times.append(t1 - t0)
        avg = sum(times) / len(times)
        print(f"⚡ {name}: avg {avg:.4f}s  (runs: {times})")

    client.close()


if __name__ == "__main__":
    benchmark()

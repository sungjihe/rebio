# scripts/benchmark_cypher.py

import time
from backend.graph.graph_search_client import GraphSearchClient


def benchmark():
    client = GraphSearchClient()

    # Example: p53
    protein = "P38398"

    # Example: Disease ID
    disease = "D012345"

    # Example: Therapeutic Protein (UniProt ID)
    tp = "P12345"

    tests = [
        ("similar_proteins", lambda: client.similar_proteins(protein, 20)),
        ("predict_diseases", lambda: client.predict_diseases(protein, 20)),
        ("recommend_therapeutics", lambda: client.recommend_therapeutics(protein, 20)),
        ("evidence_protein_disease", lambda: client.evidence_paths(protein, disease)),
        ("evidence_protein_therapeutic", lambda: client.evidence_paths(protein, tp)),
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


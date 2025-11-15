# backend/crawlers/uniprot_crawler.py
import requests


def fetch_uniprot_summary(uniprot_id: str):
    """
    UniProt KB에서 단백질 요약 정보 크롤링
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"

    res = requests.get(url, timeout=10)
    if res.status_code != 200:
        return None

    data = res.json()

    protein_name = data.get("proteinDescription", {}).get("recommendedName", {}).get("fullName", {}).get("value")

    gene_names = []
    for gene in data.get("genes", []):
        name = gene.get("geneName", {}).get("value")
        if name:
            gene_names.append(name)

    functions = []
    for comment in data.get("comments", []):
        if comment.get("type") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                functions.append(texts[0].get("value"))

    return {
        "protein_name": protein_name,
        "gene_names": gene_names,
        "functions": functions[:3]
    }

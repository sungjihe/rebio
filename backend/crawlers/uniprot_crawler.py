# backend/crawlers/uniprot_crawler.py

from backend.crawlers.common import safe_get

def fetch_uniprot_summary(uniprot_id: str):
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    res = safe_get(url)

    if not res:
        return {
            "ok": False,
            "source": "uniprot",
            "data": None,
            "error": "request_failed"
        }

    data = res.json()

    protein_name = (
        data.get("proteinDescription", {})
        .get("recommendedName", {})
        .get("fullName", {})
        .get("value")
    )

    gene_names = [
        gene.get("geneName", {}).get("value")
        for gene in data.get("genes", [])
        if gene.get("geneName", {})
    ]

    functions = []
    for comment in data.get("comments", []):
        if comment.get("type") == "FUNCTION":
            texts = comment.get("texts", [])
            if texts:
                functions.append(texts[0].get("value"))

    return {
        "ok": True,
        "source": "uniprot",
        "data": {
            "protein_name": protein_name,
            "gene_names": gene_names,
            "functions": functions[:3],
        },
        "error": None,
    }

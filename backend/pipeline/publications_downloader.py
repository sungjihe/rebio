import os
import pandas as pd
from Bio import Entrez
from .config import RAW_DATA

Entrez.email = "your@email.com"

def fetch_pubmed(query: str, retmax=20):
    handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
    ids = Entrez.read(handle)["IdList"]
    rows = []
    for pmid in ids:
        fetch = Entrez.efetch(db="pubmed", id=pmid, rettype="abstract", retmode="xml")
        article = Entrez.read(fetch)
        info = article["PubmedArticle"][0]["MedlineCitation"]["Article"]

        rows.append({
            "pmid": pmid,
            "title": info.get("ArticleTitle", ""),
            "year": info.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {}).get("Year", ""),
            "source": query
        })
    return rows

def download_publications(keywords):
    all_rows = []
    for kw in keywords:
        all_rows.extend(fetch_pubmed(kw))

    df = pd.DataFrame(all_rows)
    out_path = os.path.join(RAW_DATA, "publications.csv")
    df.to_csv(out_path, index=False)
    print(f"[OK] Saved publications → {out_path}")

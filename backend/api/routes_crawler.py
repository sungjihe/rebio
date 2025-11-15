# backend/api/routes_crawler.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from backend.crawlers.pubchem_crawler import fetch_pubchem_info
from backend.crawlers.disease_wiki_crawler import fetch_wiki_summary
from backend.crawlers.uniprot_crawler import fetch_uniprot_summary
from backend.crawlers.nct_crawler import fetch_clinical_trials

router = APIRouter(
    prefix="/external",
    tags=["External Web Crawlers"],
)


# ============================
# 1) Drug Info
# ============================
@router.get("/drug/info")
def get_drug_info(name: str):
    data = fetch_pubchem_info(name)
    if not data:
        raise HTTPException(404, f"No PubChem data found for: {name}")
    return data


# ============================
# 2) Disease Summary
# ============================
@router.get("/disease/summary")
def get_disease_summary(name: str):
    data = fetch_wiki_summary(name)
    if not data:
        raise HTTPException(404, f"No Wikipedia page for: {name}")
    return {"summary": data}


# ============================
# 3) Protein Summary
# ============================
@router.get("/protein/summary")
def get_protein_summary(uniprot_id: str):
    data = fetch_uniprot_summary(uniprot_id)
    if not data:
        raise HTTPException(404, f"No UniProt entry found for: {uniprot_id}")
    return data


# ============================
# 4) Clinical Trials
# ============================
@router.get("/clinical_trials/search")
def search_trials(query: str, max_results: int = 5):
    data = fetch_clinical_trials(query, max_results)
    if not data:
        raise HTTPException(404, f"No clinical trials found for: {query}")
    return data

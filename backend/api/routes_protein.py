# backend/api/routes_protein.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from backend.graph.graph_search_client import GraphSearchClient

router = APIRouter(
    prefix="/protein",
    tags=["Protein Analysis"],
)


# ==============================
# Request / Response Models
# ==============================

class ProteinQuery(BaseModel):
    uniprot_id: str
    top_k: Optional[int] = 20


class DiseasePredictionResponse(BaseModel):
    disease_id: str
    disease_name: str
    total_score: float
    direct_score: float
    propagated_score: float
    support_proteins: List[str]


class DrugRecommendationResponse(BaseModel):
    drugbank_id: str
    drug_name: str
    total_score: float
    direct_target_score: float
    propagated_target_score: float
    support_proteins: List[str]
    indications: List[str]


class SimilarProteinsResponse(BaseModel):
    protein_id: str
    protein_name: str
    similarity: float


# ==============================
# GraphSearchClient 인스턴스 (싱글톤)
# ==============================
client = GraphSearchClient()


# ==============================
# 1. Predict Disease API
# ==============================

@router.post("/predict_disease", response_model=List[DiseasePredictionResponse])
def predict_disease(payload: ProteinQuery):
    try:
        results = client.predict_diseases(
            uniprot_id=payload.uniprot_id,
            top_k=payload.top_k,
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 2. Recommend Drugs API
# ==============================

@router.post("/recommend_drugs", response_model=List[DrugRecommendationResponse])
def recommend_drugs(payload: ProteinQuery):
    try:
        results = client.recommend_drugs(
            uniprot_id=payload.uniprot_id,
            top_k=payload.top_k,
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==============================
# 3. Similar Proteins API
# ==============================

@router.post("/similar_proteins", response_model=List[SimilarProteinsResponse])
def similar_proteins(payload: ProteinQuery):
    try:
        results = client.similar_proteins(
            uniprot_id=payload.uniprot_id,
            top_k=payload.top_k,
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

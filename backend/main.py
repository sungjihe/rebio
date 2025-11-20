# backend/api/main.py  (또는 너의 FastAPI 엔트리 파일)

from fastapi import FastAPI

from backend.api.routes_rebio import router as rebio_router
from backend.api.routes_protein import router as protein_router

app = FastAPI(title="ReBio Multi-Agent API")

# 기존 ReBio Q&A (graph 기반)
app.include_router(rebio_router, prefix="/rebio")

# 새 Protein Sequence Analyzer
app.include_router(protein_router)  # prefix는 routes_protein 안에 이미 "/protein"으로 있음


@app.get("/")
def root():
    return {"message": "ReBio Multi-Agent API is running."}


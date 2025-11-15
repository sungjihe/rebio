# backend/main.py
import sys
import os

# 현재 파일(backend/main.py)의 상위 폴더(`/workspace/rebio`)를 Python 경로에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 너가 만든 protein route
from backend.api.routes_protein import router as protein_router

# 내가 만든 crawler route
from backend.api.routes_crawler import router as crawler_router


# =======================================
# FastAPI App
# =======================================
app = FastAPI(
    title="ReBio API",
    version="1.0",
    description="Protein-based Disease/Drug Prediction + Web Crawler APIs"
)


# =======================================
# CORS (Streamlit, 프론트엔드 가능)
# =======================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =======================================
# Register Routers
# =======================================
app.include_router(protein_router)   # /protein/*
app.include_router(crawler_router)   # /external/*


# =======================================
# Health Check
# =======================================
@app.get("/")
def root():
    return {"status": "ok", "message": "ReBio API running!"}


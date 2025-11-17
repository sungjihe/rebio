# backend/main.py
import sys
import os

# backend/main.py → 프로젝트 root를 sys.path에 추가
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Protein graph routes
from backend.api.routes_protein import router as protein_router

# External web crawlers
from backend.api.routes_crawler import router as crawler_router

# ★ Workflow (Chat) API — 추가해야 함
from backend.api.routes_chat import router as chat_router


# ---------------------------------------
# FastAPI App
# ---------------------------------------
app = FastAPI(
    title="ReBio API",
    version="1.0",
    description="Protein Reasoning + Evidence Graph + Web Crawler + Redesign Workflow",
)


# ---------------------------------------
# CORS 설정 (Streamlit/프론트엔드 허용)
# ---------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------
# Router 등록
# ---------------------------------------
app.include_router(protein_router)     # /protein/*
app.include_router(crawler_router)     # /external/*
app.include_router(chat_router)        # /chat/run_workflow   ← ★ 반드시 필요


# ---------------------------------------
# Health Check
# ---------------------------------------
@app.get("/")
def root():
    return {"status": "ok", "message": "ReBio API running!"}

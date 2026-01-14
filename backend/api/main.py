# backend/api/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ReBio routes
from backend.api.routes_rebio import router as rebio_router
from backend.api.routes_protein import router as protein_router

app = FastAPI(
    title="ReBio API",
    version="1.0.0",
    description="ReBio Multi-Agent System Backend API"
)

# CORS (Streamlit + RunPod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ prefix는 routes_*에서만 관리
app.include_router(rebio_router)
app.include_router(protein_router)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "ReBio API backend running."
    }

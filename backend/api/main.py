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

# Routers
app.include_router(rebio_router, prefix="/rebio")
app.include_router(protein_router, prefix="/protein")


@app.get("/")
def root():
    return {"status": "ok", "message": "ReBio API backend running."}


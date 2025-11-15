# backend/api/routes_chat.py
from fastapi import APIRouter
from pydantic import BaseModel

from backend.graph_workflow.workflow import run_workflow

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatQuery(BaseModel):
    query: str
    top_k: int = 10

@router.post("/run_workflow")
def run_chat(payload: ChatQuery):
    return run_workflow(payload.query, payload.top_k)

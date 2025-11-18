# backend/api/routes_rebio.py

from fastapi import APIRouter
from pydantic import BaseModel

from backend.agentic.workflow import run_helicon

router = APIRouter(
    prefix="/rebio",
    tags=["ReBio Multi-Agent Workflow"]
)

class ReBioQuery(BaseModel):
    question: str


@router.post("/run")
async def run_rebio_workflow(payload: ReBioQuery):
    """
    ReBio Multi-Agent Workflow Entry Point
    """
    result = run_helicon(payload.question)
    return result

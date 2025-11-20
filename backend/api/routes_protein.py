# backend/api/routes_protein.py

from fastapi import APIRouter
from pydantic import BaseModel

from backend.agentic.sequence_workflow import run_sequence_pipeline

router = APIRouter(
    prefix="/protein",
    tags=["Protein Sequence Analysis"],
)


class SequenceQuery(BaseModel):
    sequence: str


@router.post("/analyze")
async def analyze_protein(payload: SequenceQuery):
    """
    ProteinAnalyzer 전용 엔드포인트
    - 입력: sequence (string)
    - 출력: FinalNode에서 생성한 final_output(JSON)
    """
    result = run_sequence_pipeline(payload.sequence)
    return result

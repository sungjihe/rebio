# backend/agentic/sequence_workflow.py

import logging
from backend.agentic.state import HeliconState
from backend.agentic.nodes.design_node import DesignNode
from backend.agentic.nodes.structure_node import StructureNode
from backend.agentic.nodes.reasoner_node import ReasonerNode
from backend.agentic.nodes.final_node import FinalNode

logger = logging.getLogger("SequenceWorkflow")


def _clean_sequence(seq: str) -> str:
    """공백/개행 제거 + 대문자 정규화"""
    return (
        seq.replace(" ", "")
           .replace("\n", "")
           .replace("\r", "")
           .upper()
    )


def run_sequence_pipeline(sequence: str) -> dict:
    """
    ProteinAnalyzer 전용 시퀀스 파이프라인:
    Sequence → DesignNode → StructureNode → ReasonerNode → FinalNode

    반환값은 FinalNode에서 생성한 final_output(JSON dict)을 그대로 리턴.
    """
    seq_clean = _clean_sequence(sequence)

    # 초기 State 구성
    state = HeliconState(
        question="Protein sequence analysis (sequence-only workflow).",
        image_path=None,
    )
    state.intent = "protein_design"
    state.entities = {"protein_sequence": seq_clean}

    logger.info("[SequenceWorkflow] Start sequence-only pipeline")

    # 1) Design (변이 설계)
    design_node = DesignNode()
    state = design_node.run(state)

    # 2) Structure (ESMFold / 구조 예측)
    structure_node = StructureNode()
    state = structure_node.run(state)

    # 3) Reasoning (GPT-4o + BioMistral 통합 추론)
    reasoner_node = ReasonerNode()
    state = reasoner_node.run(state)

    # 4) Final (Markdown + JSON 조립)
    final_node = FinalNode()
    state = final_node.run(state)

    # FinalNode가 만든 JSON 패킷
    final_output = getattr(state, "final_output", None)
    if final_output is None:
        # 안전 장치: final_output이 없으면 최소 정보 패킷 만들어서 반환
        final_output = {
            "intent": state.intent,
            "entities": state.entities,
            "designed_protein": getattr(state, "designed_protein", None),
            "structure_result": getattr(state, "structure_result", None),
            "reasoning_summary": getattr(state, "reasoning_summary", None),
            "reasoning_scientific": getattr(state, "reasoning", None),
        }

    # ProteinAnalyzer 편의를 위한 alias 몇 개 추가
    final_output.setdefault("input_sequence", seq_clean)

    # 구조 텍스트 alias (있으면)
    structure = final_output.get("structure_result") or {}
    pdb_text = structure.get("pdb_text") or structure.get("pdb") or None
    if pdb_text:
        final_output.setdefault("pdb_text", pdb_text)

    # 리포트 markdown alias
    if "markdown_summary" in final_output and final_output["markdown_summary"]:
        final_output.setdefault("summary_markdown", final_output["markdown_summary"])

    # 디자인 alias: 기존 UI 호환용
    if "designed_protein" in final_output and final_output["designed_protein"] is not None:
        final_output.setdefault(
            "design_result",
            {
                "original_sequence": seq_clean,
                "variants": final_output["designed_protein"],
            },
        )

    logger.info("[SequenceWorkflow] Finished sequence-only pipeline")
    return final_output

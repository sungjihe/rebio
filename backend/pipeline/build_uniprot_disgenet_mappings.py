# backend/pipeline/build_uniprot_disgenet_mappings.py

import csv
import os
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional

from dotenv import load_dotenv

# ReBio 공용 경로 설정 (config 재사용)
from backend.pipeline.config import RAW_DATA_ROOT, PROCESSED_DATA_ROOT

# ================================
# 로깅 설정
# ================================
logger = logging.getLogger("build_uniprot_disgenet_mappings")
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")

# ================================
# 환경 변수 로드
# ================================
BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

# 기본 파일 경로
DEFAULT_PROTEINS_CSV = RAW_DATA_ROOT / "proteins.csv"              # ⭐ 너의 파일명에 맞춰 조정
DEFAULT_DISGENET_TSV = RAW_DATA_ROOT / "disgenet_gene_disease.tsv"
DEFAULT_OUTPUT_CSV = PROCESSED_DATA_ROOT / "disease_associations.csv"


# =========================================================
# 1) proteins.csv → gene_symbol → [uniprot_ids] 매핑
# =========================================================
def load_protein_gene_map(
    proteins_csv: Path,
    gene_col_candidates: List[str] = None,
) -> Dict[str, List[str]]:
    """
    protein.csv에서 gene symbol을 읽어
    gene_symbol → [uniprot_id1, uniprot_id2] 매핑 생성
    """

    if gene_col_candidates is None:
        # 너의 CSV 구조 기반: gene 컬럼만 있어도 동작
        gene_col_candidates = ["gene_symbol", "gene", "symbol"]

    if not proteins_csv.exists():
        raise FileNotFoundError(f"proteins.csv not found: {proteins_csv}")

    gene_to_uniprot: Dict[str, List[str]] = {}

    with proteins_csv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []

        # gene 컬럼 탐색
        gene_col = None
        for c in gene_col_candidates:
            if c in header:
                gene_col = c
                break

        if gene_col is None:
            raise ValueError(
                f"proteins.csv에서 gene symbol 컬럼이 없습니다. "
                f"지원 컬럼: {gene_col_candidates}, 실제: {header}"
            )

        if "uniprot_id" not in header:
            raise ValueError("proteins.csv에 'uniprot_id' 컬럼이 필요합니다.")

        for row in reader:
            uid = (row.get("uniprot_id") or "").strip()
            gene = (row.get(gene_col) or "").strip()

            if not uid or not gene:
                continue

            # ⭐ normalize (CD86 vs Cd86 문제 해결)
            gene = gene.upper()

            gene_to_uniprot.setdefault(gene, []).append(uid)

    logger.info(
        f"[load_protein_gene_map] Loaded {len(gene_to_uniprot)} genes from {proteins_csv}"
    )
    return gene_to_uniprot


# =========================================================
# 2) build association (DisGeNET geneSymbol → UniProt 매핑)
# =========================================================
def build_uniprot_disease_associations(
    disgenet_tsv: Path,
    gene_to_uniprot: Dict[str, List[str]],
    min_score: float = 0.1,
) -> Dict[Tuple[str, str], Dict[str, Any]]:

    if not disgenet_tsv.exists():
        raise FileNotFoundError(f"DisGeNET TSV not found: {disgenet_tsv}")

    associations: Dict[Tuple[str, str], Dict[str, Any]] = {}

    with disgenet_tsv.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        fieldnames = reader.fieldnames or []

        # 필드 이름
        gene_col = "geneSymbol" if "geneSymbol" in fieldnames else None
        disease_id_col = "diseaseId" if "diseaseId" in fieldnames else None
        score_col = "score" if "score" in fieldnames else None
        source_col = "source" if "source" in fieldnames else None
        dtype_col = "diseaseType" if "diseaseType" in fieldnames else None
        pmids_col = "pmids" if "pmids" in fieldnames else None

        if not gene_col or not disease_id_col:
            raise ValueError(
                f"DisGeNET TSV에 geneSymbol/diseaseId가 없습니다. 헤더: {fieldnames}"
            )

        count_total = 0
        count_mapped = 0

        for row in reader:
            count_total += 1

            # ⭐ geneSymbol normalize
            gene = (row.get(gene_col) or "").strip().upper()

            if not gene:
                continue

            if gene not in gene_to_uniprot:
                # proteins.csv에 존재하지 않는 유전자 → 스킵
                continue

            disease_id = (row.get(disease_id_col) or "").strip()
            if not disease_id:
                continue

            # score
            raw_score = (row.get(score_col) or "").strip() if score_col else ""
            try:
                score = float(raw_score) if raw_score not in ("", "NA") else 1.0
            except ValueError:
                score = 1.0

            if score < min_score:
                continue

            source = (row.get(source_col) or "").strip() if source_col else "DisGeNET"
            disease_type = (row.get(dtype_col) or "").strip() if dtype_col else ""
            pmids = (row.get(pmids_col) or "").strip() if pmids_col else ""

            evidence_type = disease_type or "unknown"

            reference = ""
            if pmids:
                pmid_list = [p.strip() for p in pmids.replace(";", ",").split(",") if p.strip()]
                if pmid_list:
                    reference = "PMID:" + ";".join(pmid_list)

            # 해당 geneSymbol -> proteins.csv에 존재하는 모든 UniProt 연결
            for uid in gene_to_uniprot[gene]:
                key = (uid, disease_id)
                assoc = associations.get(key)

                if assoc is None:
                    associations[key] = {
                        "uniprot_id": uid,
                        "disease_id": disease_id,
                        "score": score,
                        "sources": set([source]),
                        "evidence_types": set([evidence_type]),
                        "references": set([reference]) if reference else set(),
                    }
                else:
                    # 최대 score
                    assoc["score"] = max(assoc["score"], score)
                    if source:
                        assoc["sources"].add(source)
                    if evidence_type:
                        assoc["evidence_types"].add(evidence_type)
                    if reference:
                        assoc["references"].add(reference)

                count_mapped += 1

        logger.info(
            f"[build_uniprot_disease_associations] Total rows: {count_total}, "
            f"mapped: {count_mapped}, unique pairs: {len(associations)}"
        )

    return associations


# =========================================================
# 3) 결과 CSV 저장
# =========================================================
def save_associations_to_csv(
    associations: Dict[Tuple[str, str], Dict[str, Any]],
    output_csv: Path,
):
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "uniprot_id",
                "disease_id",
                "score",
                "source",
                "evidence_type",
                "reference",
                "active",
            ]
        )

        for (uid, did), info in associations.items():
            sources = ";".join(sorted(info["sources"])) if info["sources"] else ""
            evidence_types = ";".join(sorted(info["evidence_types"])) if info["evidence_types"] else ""
            references = ";".join(sorted(info["references"])) if info["references"] else ""

            writer.writerow(
                [
                    uid,
                    did,
                    f"{info['score']:.4f}",
                    sources or "DisGeNET",
                    evidence_types or "unknown",
                    references,
                    "true",
                ]
            )

    logger.info(f"[save_associations_to_csv] Saved {len(associations)} rows → {output_csv}")


# =========================================================
# 4) run() + CLI
# =========================================================
def run_build_uniprot_disgenet(
    proteins_csv: Path = DEFAULT_PROTEINS_CSV,
    disgenet_tsv: Path = DEFAULT_DISGENET_TSV,
    output_csv: Path = DEFAULT_OUTPUT_CSV,
    min_score: float = 0.1,
):
    logger.info(f"[RUN] proteins_csv = {proteins_csv}")
    logger.info(f"[RUN] disgenet_tsv = {disgenet_tsv}")
    logger.info(f"[RUN] output_csv   = {output_csv}")

    gene_map = load_protein_gene_map(proteins_csv)
    associations = build_uniprot_disease_associations(disgenet_tsv, gene_map, min_score=min_score)
    save_associations_to_csv(associations, output_csv)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Build UniProt–Disease associations from protein.csv + DisGeNET TSV"
    )
    parser.add_argument("--proteins_csv", type=str, default=str(DEFAULT_PROTEINS_CSV))
    parser.add_argument("--disgenet_tsv", type=str, default=str(DEFAULT_DISGENET_TSV))
    parser.add_argument("--output_csv", type=str, default=str(DEFAULT_OUTPUT_CSV))
    parser.add_argument("--min_score", type=float, default=0.1)

    args = parser.parse_args()

    run_build_uniprot_disgenet(
        proteins_csv=Path(args.proteins_csv),
        disgenet_tsv=Path(args.disgenet_tsv),
        output_csv=Path(args.output_csv),
        min_score=args.min_score,
    )

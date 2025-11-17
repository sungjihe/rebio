# backend/agent/relation_weighting_node.py

import os
import json
import logging
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field, validator

from sklearn.linear_model import Ridge
from sklearn.model_selection import train_test_split

logger = logging.getLogger("RelationWeightingNode")
logging.basicConfig(level=logging.INFO)


# ======================================================
# 1) 데이터 스키마 정의
# ======================================================

class RelationTrainingExample(BaseModel):
    """
    한 개의 후보(disease 또는 drug)에 대한 학습 샘플
    """
    task: str = Field(..., description="disease_prediction | drug_recommendation")
    direct_score: float
    propagated_score: float
    label: float = Field(..., description="ground truth (0~1 또는 0/1)")

    @validator("task")
    def validate_task(cls, v: str) -> str:
        allowed = {"disease_prediction", "drug_recommendation"}
        if v not in allowed:
            raise ValueError(f"task must be one of {allowed}, got {v}")
        return v


class RelationWeights(BaseModel):
    """
    direct / propagated score에 대한 최종 weight 세트
    """
    w_direct: float = 0.7
    w_propagated: float = 0.3
    bias: float = 0.0  # 필요시 offset 용도

    def combine(self, direct_score: float, propagated_score: float) -> float:
        return self.w_direct * direct_score + self.w_propagated * propagated_score + self.bias


class RelationWeightingConfig(BaseModel):
    """
    태스크별 weight set
    """
    disease_prediction: RelationWeights = RelationWeights(w_direct=0.7, w_propagated=0.3, bias=0.0)
    drug_recommendation: RelationWeights = RelationWeights(w_direct=0.7, w_propagated=0.3, bias=0.0)


# ======================================================
# 2) RelationWeightingNode 본체
# ======================================================

class RelationWeightingNode:
    """
    ReBio Relation Weighting 자동 학습 노드

    역할:
    - disease_prediction / drug_recommendation 태스크에 대해
      direct_score / propagated_score를 최적으로 조합하는 weight를 학습
    - 학습 결과를 JSON으로 저장 / 로드
    - 런타임에 total_score 재계산에 사용

    내부 모델:
    - 현재는 단순 Ridge(선형 회귀, L2 정규화) 기반
    - 나중에 MLP, GNN, LoRA 등으로 교체 가능 (API 유지)
    """

    def __init__(
        self,
        weights_path: Optional[str] = None,
    ):
        """
        weights_path: 학습된 weight JSON이 저장된 경로
        """
        self.weights_path = weights_path or os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "processed",
            "relation_weights.json",
        )

        # 태스크별 weight config (초기에는 default)
        self.config: RelationWeightingConfig = RelationWeightingConfig()

        # 태스크별 회귀 모델 (원하면 나중에 inference에도 사용)
        self.models: Dict[str, Ridge] = {}

        # 기존 weight 파일이 있으면 로드
        if os.path.exists(self.weights_path):
            self._load_weights()

    # --------------------------------------------------
    # 2-1) 내부: weight 저장/로드
    # --------------------------------------------------
    def _save_weights(self):
        data = self.config.model_dump()
        os.makedirs(os.path.dirname(self.weights_path), exist_ok=True)
        with open(self.weights_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"[RelationWeightingNode] Weights saved → {self.weights_path}")

    def _load_weights(self):
        with open(self.weights_path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        self.config = RelationWeightingConfig(**raw)
        logger.info(f"[RelationWeightingNode] Loaded weights from {self.weights_path}")

    # --------------------------------------------------
    # 2-2) 학습 데이터 로드 (JSONL)
    # --------------------------------------------------
    @staticmethod
    def load_training_data(jsonl_path: str) -> List[RelationTrainingExample]:
        if not os.path.exists(jsonl_path):
            raise FileNotFoundError(f"Training file not found: {jsonl_path}")

        examples: List[RelationTrainingExample] = []
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    ex = RelationTrainingExample(**obj)
                    examples.append(ex)
                except Exception as e:
                    logger.warning(f"[RelationWeightingNode] Skip line {line_no}: {e}")
        logger.info(f"[RelationWeightingNode] Loaded {len(examples)} training examples from {jsonl_path}")
        return examples

    # --------------------------------------------------
    # 2-3) 태스크별로 학습 (Ridge 회귀)
    # --------------------------------------------------
    def _train_for_task(self, task: str, examples: List[RelationTrainingExample]) -> RelationWeights:
        xs = []
        ys = []

        for ex in examples:
            if ex.task != task:
                continue
            xs.append([ex.direct_score, ex.propagated_score])
            ys.append(ex.label)

        if not xs:
            logger.warning(f"[RelationWeightingNode] No examples for task={task}. Use default weights.")
            # 그냥 기존 config 유지
            return getattr(self.config, task)

        X_train, X_val, y_train, y_val = train_test_split(xs, ys, test_size=0.2, random_state=42)

        # 간단한 Ridge 회귀: L2 정규화로 weight 안정화
        model = Ridge(alpha=0.1, fit_intercept=True, random_state=42)
        model.fit(X_train, y_train)

        # 간단한 validation log
        val_pred = model.predict(X_val)
        mse = sum((p - y)**2 for p, y in zip(val_pred, y_val)) / len(y_val) if y_val else 0.0
        logger.info(f"[RelationWeightingNode] Task={task} trained. Val MSE={mse:.4f}")

        self.models[task] = model

        # 계수 추출 → RelationWeights로 변환
        w_direct, w_prop = model.coef_
        bias = float(model.intercept_)

        logger.info(
            f"[RelationWeightingNode] Task={task} learned weights: "
            f"w_direct={w_direct:.4f}, w_prop={w_prop:.4f}, bias={bias:.4f}"
        )

        # config 객체 갱신
        new_weights = RelationWeights(
            w_direct=float(w_direct),
            w_propagated=float(w_prop),
            bias=bias,
        )
        return new_weights

    # --------------------------------------------------
    # 2-4) 전체 학습 엔트리포인트
    # --------------------------------------------------
    def fit_from_jsonl(self, jsonl_path: str):
        """
        전체 학습 파이프라인
        - JSONL에서 데이터 읽고
        - task별로 weight 학습
        - config + weights 저장
        """
        examples = self.load_training_data(jsonl_path)

        # disease_prediction
        new_disease_weights = self._train_for_task("disease_prediction", examples)
        self.config.disease_prediction = new_disease_weights

        # drug_recommendation
        new_drug_weights = self._train_for_task("drug_recommendation", examples)
        self.config.drug_recommendation = new_drug_weights

        # 저장
        self._save_weights()

    # --------------------------------------------------
    # 2-5) 런타임 scoring API
    # --------------------------------------------------
    def score(
        self,
        task: str,
        direct_score: float,
        propagated_score: float,
        clip_to_01: bool = True,
    ) -> float:
        """
        학습된 weight를 사용해 total_score를 계산

        예:
            node.score("disease_prediction", direct_score=0.8, propagated_score=0.3)
        """
        if task not in ("disease_prediction", "drug_recommendation"):
            raise ValueError(f"Unknown task: {task}")

        w: RelationWeights = getattr(self.config, task)
        total = w.combine(direct_score, propagated_score)

        if clip_to_01:
            total = max(0.0, min(1.0, total))

        return total


# ======================================================
# 3) CLI / 스크립트 모드
# ======================================================

if __name__ == "__main__":
    """
    예시 실행:

    (venv) python -m backend.agent.relation_weighting_node \
        data/processed/relation_weight_training.jsonl

    처럼 실행했을 때를 가정해서, 간단한 CLI도 넣어둠.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Train relation weighting model from JSONL")
    parser.add_argument(
        "train_jsonl",
        type=str,
        help="path to relation_weight_training.jsonl",
    )
    parser.add_argument(
        "--weights_path",
        type=str,
        default=None,
        help="path to save weights json (default: data/processed/relation_weights.json)",
    )

    args = parser.parse_args()

    node = RelationWeightingNode(weights_path=args.weights_path)
    node.fit_from_jsonl(args.train_jsonl)
    logger.info("✅ RelationWeightingNode training completed.")

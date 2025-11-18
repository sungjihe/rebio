# backend/pipeline/steps/step_graph.py

from backend.config import Config
from backend.graph.builder import build_full_graph


def run():
    """
    data/raw/*.csv 를 Neo4j에 로딩
    - 노드 + 관계 모두 포함
    """
    print("🧱 [STEP: graph] Neo4j 그래프 빌드 시작")
    build_full_graph(data_root=Config.RAW_DATA_ROOT)
    print("✅ [STEP: graph] 완료")

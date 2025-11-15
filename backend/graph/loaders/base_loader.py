# backend/graph/loaders/base_loader.py
from abc import ABC, abstractmethod
from typing import Iterable, Dict, Any, List

from neo4j import Driver

from .utils import get_driver, batched, read_csv_dicts, read_jsonl_dicts, logger


class BaseLoader(ABC):
    """
    공통 Loader 베이스:
      - CSV / JSONL 읽기
      - batch 삽입
    """

    def __init__(self, driver: Driver | None = None, batch_size: int = 500):
        self.driver = driver or get_driver()
        self.batch_size = batch_size
        self.log = logger.getChild(self.__class__.__name__)

    # ------------------------
    # 외부 API
    # ------------------------
    def load_from_csv(self, path: str) -> None:
        rows = read_csv_dicts(path)
        self._load_from_iter(rows)

    def load_from_jsonl(self, path: str) -> None:
        rows = read_jsonl_dicts(path)
        self._load_from_iter(rows)

    def load_from_records(self, records: Iterable[Dict[str, Any]]) -> None:
        self._load_from_iter(records)

    # ------------------------
    # 내부 공통 로직
    # ------------------------
    def _load_from_iter(self, rows: Iterable[Dict[str, Any]]) -> None:
        total = 0
        with self.driver.session() as session:
            for batch in batched(rows, self.batch_size):
                batch = [self._preprocess_row(r) for r in batch]
                cypher, params = self._prepare_cypher_and_params(batch)
                self.log.info(f"Writing batch size={len(batch)}")
                session.execute_write(lambda tx: tx.run(cypher, **params))
                total += len(batch)
        self.log.info(f"Done. Total rows inserted/merged: {total}")

    @abstractmethod
    def _prepare_cypher_and_params(self, batch: List[Dict[str, Any]]) -> tuple[str, Dict[str, Any]]:
        """
        각 Loader에서 Cypher와 파라미터 생성
        """
        ...

    def _preprocess_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        타입 변환/전처리. 필요 없으면 그대로 반환.
        """
        return row

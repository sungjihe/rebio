# backend/graph/loaders/utils.py
import os
import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime, date
from typing import Iterable, List, Dict, Any, Generator, Optional

from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv, find_dotenv

# -----------------------------
# 환경 변수 로드 (.env)
# -----------------------------
load_dotenv(find_dotenv())

# -----------------------------
# 로깅 기본 설정
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s",
)

logger = logging.getLogger("graph_loader")


# -----------------------------
# Neo4j Config & Driver
# -----------------------------
@dataclass
class Neo4jConfig:
    uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user: str = os.getenv("NEO4J_USER", "neo4j")
    password: str = os.getenv("NEO4J_PASSWORD", "password")


_driver: Optional[Driver] = None


def get_driver() -> Driver:
    """
    싱글톤 패턴으로 neo4j.Driver 제공
    """
    global _driver
    if _driver is None:
        cfg = Neo4jConfig()
        logger.info(f"Connecting to Neo4j at {cfg.uri} as {cfg.user}")
        _driver = GraphDatabase.driver(cfg.uri, auth=(cfg.user, cfg.password))
    return _driver


def close_driver():
    global _driver
    if _driver is not None:
        logger.info("Closing Neo4j driver")
        _driver.close()
        _driver = None


# -----------------------------
# 타입 변환 유틸
# -----------------------------
def parse_bool(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    if s in ("true", "1", "yes", "y"):
        return True
    if s in ("false", "0", "no", "n"):
        return False
    return None


def parse_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def parse_date(value: Any) -> Optional[date]:
    """
    YYYY-MM-DD, YYYY/MM/DD 등 단순 포맷 지원
    """
    if not value:
        return None
    s = str(value).strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_list_str(value: Any, sep: str = ";") -> List[str]:
    """
    'a;b;c' → ['a', 'b', 'c']
    """
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if v not in (None, "")]
    s = str(value).strip()
    if not s:
        return []
    return [x.strip() for x in s.split(sep) if x.strip()]


# -----------------------------
# 배치 유틸
# -----------------------------
def batched(iterable: Iterable[Dict[str, Any]], batch_size: int) -> Generator[List[Dict[str, Any]], None, None]:
    batch: List[Dict[str, Any]] = []
    for item in iterable:
        batch.append(item)
        if len(batch) >= batch_size:
            yield batch
            batch = []
    if batch:
        yield batch


# -----------------------------
# CSV / JSONL 로더
# -----------------------------
def read_csv_dicts(path: str, encoding: str = "utf-8") -> Iterable[Dict[str, Any]]:
    logger.info(f"Reading CSV: {path}")
    with open(path, newline="", encoding=encoding) as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield row


def read_jsonl_dicts(path: str, encoding: str = "utf-8") -> Iterable[Dict[str, Any]]:
    """
    JSON Lines 형식: 한 줄에 하나의 JSON 객체
    """
    logger.info(f"Reading JSONL: {path}")
    with open(path, encoding=encoding) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

# backend/crawlers/common.py
import requests
import logging

logger = logging.getLogger("Crawler")
logging.basicConfig(level=logging.INFO)

HEADERS = {
    "User-Agent": "ReBioCrawler/1.0 (+https://github.com/sungjihe/rebio)"
}

def safe_get(url: str, timeout: float = 10):
    """統合 HTTP GET wrapper: timeout + user-agent + 예외 처리"""
    try:
        res = requests.get(url, timeout=timeout, headers=HEADERS)
        res.raise_for_status()
        return res
    except Exception as e:
        logger.warning(f"[Crawler] GET failed: {url} -> {e}")
        return None

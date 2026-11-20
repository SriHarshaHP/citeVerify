import os
import json
import hashlib
from typing import Any, Optional
from pathlib import Path
from app.config import settings

class DiskCache:
    """Disk-backed hash-based cache for HTTP and LLM calls."""
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = Path(cache_dir or settings.CACHE_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.http_dir = self.cache_dir / "http"
        self.llm_dir = self.cache_dir / "llm"
        self.http_dir.mkdir(parents=True, exist_ok=True)
        self.llm_dir.mkdir(parents=True, exist_ok=True)

    def _hash_key(self, namespace: str, key_data: Any) -> str:
        if isinstance(key_data, dict) or isinstance(key_data, list):
            serialized = json.dumps(key_data, sort_keys=True)
        else:
            serialized = str(key_data)
        hasher = hashlib.sha256()
        hasher.update(namespace.encode("utf-8"))
        hasher.update(b":")
        hasher.update(serialized.encode("utf-8"))
        return hasher.hexdigest()

    def get_http(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        key = self._hash_key("http", {"url": url, "params": params or {}})
        cache_file = self.http_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set_http(self, url: str, params: Optional[dict], data: Any) -> None:
        key = self._hash_key("http", {"url": url, "params": params or {}})
        cache_file = self.http_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def get_llm(self, prompt: str, model: str) -> Optional[dict]:
        key = self._hash_key("llm", {"prompt": prompt, "model": model})
        cache_file = self.llm_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def set_llm(self, prompt: str, model: str, response: dict) -> None:
        key = self._hash_key("llm", {"prompt": prompt, "model": model})
        cache_file = self.llm_dir / f"{key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(response, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

cache = DiskCache()

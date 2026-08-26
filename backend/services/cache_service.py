"""Cache service for GenshinIQ account showcases and data."""

import json
import time
from pathlib import Path
from typing import Optional, Dict, Any
from backend.config import settings

SHOWCASE_CACHE_DIR = Path("data/raw/showcases")


class ShowcaseCacheService:
    """Manages TTL-aware caching for Enka API player showcases."""

    def __init__(self, cache_dir: Path = SHOWCASE_CACHE_DIR):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # In-memory fast cache: { uid: (expires_at, data) }
        self._memory_cache: Dict[str, tuple[float, Dict[str, Any]]] = {}

    def get(self, uid: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached showcase if still within TTL."""
        now = time.time()

        # Check in-memory first
        if uid in self._memory_cache:
            expires_at, data = self._memory_cache[uid]
            if now < expires_at:
                return data
            else:
                del self._memory_cache[uid]

        # Check disk cache
        cache_file = self.cache_dir / f"{uid}.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    entry = json.load(f)
                expires_at = entry.get("_cached_expires_at", 0)
                if now < expires_at:
                    data = entry.get("data", {})
                    # Populate memory cache
                    self._memory_cache[uid] = (expires_at, data)
                    return data
            except Exception:
                pass

        return None

    def set(self, uid: str, data: Dict[str, Any], ttl_seconds: Optional[int] = None) -> None:
        """Store showcase in memory and on disk with TTL."""
        ttl = ttl_seconds if ttl_seconds is not None else settings.ENKA_CACHE_TTL_SECONDS
        expires_at = time.time() + ttl

        # Save to memory
        self._memory_cache[uid] = (expires_at, data)

        # Save to disk
        cache_file = self.cache_dir / f"{uid}.json"
        try:
            entry = {
                "_cached_at": time.time(),
                "_cached_expires_at": expires_at,
                "ttl": ttl,
                "data": data,
            }
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(entry, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def invalidate(self, uid: str) -> None:
        """Invalidate cache for a UID."""
        if uid in self._memory_cache:
            del self._memory_cache[uid]
        cache_file = self.cache_dir / f"{uid}.json"
        if cache_file.exists():
            try:
                cache_file.unlink()
            except Exception:
                pass


cache_service = ShowcaseCacheService()

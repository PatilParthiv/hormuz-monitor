"""In-memory cache module for the Hormuz Monitor backend.

Strictly in-memory: No database is used.
Provides thread-safe TTL caching and fallback access to the most recent successful data.
"""

import threading
from typing import Any, Optional
from cachetools import TTLCache


class InMemoryCache:
    """Thread-safe in-memory cache with TTL expiration and fallback memory."""

    def __init__(self, maxsize: int = 128, ttl_seconds: int = 1800):
        self._ttl = ttl_seconds
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl_seconds)
        self._last_successful: dict[str, Any] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve item if not expired, or return None."""
        with self._lock:
            return self._cache.get(key)

    def set(self, key: str, value: Any) -> None:
        """Store item with TTL and update last successful fallback copy."""
        with self._lock:
            self._cache[key] = value
            self._last_successful[key] = value

    def get_last_successful(self, key: str) -> Optional[Any]:
        """Retrieve the latest successful value even if the TTL has expired."""
        with self._lock:
            return self._last_successful.get(key)

    def clear(self) -> None:
        """Clear both active cache and fallback stores."""
        with self._lock:
            self._cache.clear()
            self._last_successful.clear()


# Global cache instance for Brent oil prices (30 minute TTL)
brent_cache = InMemoryCache(maxsize=16, ttl_seconds=1800)

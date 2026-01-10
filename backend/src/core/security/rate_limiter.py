import time
from collections import defaultdict
from threading import Lock

class RateLimiter:
    """
    Token Bucket implementation for rate limiting.
    Tracks usage by identifier (IP or Session Token).
    Performs periodic cleanup of old entries.
    """
    def __init__(self):
        self._buckets = defaultdict(lambda: {"tokens": 0, "last_refill": time.time()})
        self._lock = Lock()
        self._cleanup_interval = 300 # 5 minutes
        self._last_cleanup = time.time()

    def is_allowed(self, identifier: str, capacity: int, refill_rate_per_second: float) -> bool:
        """
        Check if a request is allowed.
        :param identifier: Unique ID (IP address or Session ID)
        :param capacity: Max burst tokens
        :param refill_rate_per_second: Tokens added per second
        :return: True if allowed, False if limited
        """
        with self._lock:
            now = time.time()
            self._cleanup_if_needed(now)
            
            bucket = self._buckets[identifier]
            
            # Refill
            elapsed = now - bucket["last_refill"]
            tokens_to_add = elapsed * refill_rate_per_second
            bucket["tokens"] = min(capacity, bucket["tokens"] + tokens_to_add)
            bucket["last_refill"] = now
            
            # Consume
            if bucket["tokens"] >= 1:
                bucket["tokens"] -= 1
                return True
            
            return False

    def _cleanup_if_needed(self, now: float):
        if now - self._last_cleanup > self._cleanup_interval:
            # simple cleanup of stale buckets
            # iterating copy to avoid runtime errors
            for key in list(self._buckets.keys()):
                 if now - self._buckets[key]["last_refill"] > 3600: # 1 hour inactive
                     del self._buckets[key]
            self._last_cleanup = now

# Global instance
rate_limiter = RateLimiter()

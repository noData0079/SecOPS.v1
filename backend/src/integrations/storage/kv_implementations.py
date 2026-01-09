# backend/src/integrations/storage/kv_implementations.py

"""Concrete implementations of KVCache for different storage backends."""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from .kv_cache import KVCache

logger = logging.getLogger(__name__)


class RedisKVCache(KVCache):
    """Redis-based key-value cache implementation."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0, **kwargs):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            db: Redis database number
            **kwargs: Additional Redis client parameters
        """
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Run: pip install redis")
        
        self.client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            **kwargs
        )
        logger.info(f"RedisKVCache initialized: {host}:{port}/{db}")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a key-value pair with optional TTL in seconds."""
        try:
            serialized = json.dumps(value)
            if ttl:
                self.client.setex(key, ttl, serialized)
            else:
                self.client.set(key, serialized)
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            raise
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key, returns None if not found."""
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for key {key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None
    
    def delete(self, key: str) -> None:
        """Delete a key."""
        try:
            self.client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")


class InMemoryKVCache(KVCache):
    """In-memory dictionary-based cache (for development/testing)."""
    
    def __init__(self):
        """Initialize in-memory cache."""
        self._store: Dict[str, tuple[Any, Optional[datetime]]] = {}
        logger.info("InMemoryKVCache initialized")
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a key-value pair with optional TTL in seconds."""
        expiry = None
        if ttl:
            expiry = datetime.utcnow() + timedelta(seconds=ttl)
        self._store[key] = (value, expiry)
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key, returns None if not found or expired."""
        if key not in self._store:
            return None
        
        value, expiry = self._store[key]
        
        # Check if expired
        if expiry and datetime.utcnow() > expiry:
            del self._store[key]
            return None
        
        return value
    
    def delete(self, key: str) -> None:
        """Delete a key."""
        if key in self._store:
            del self._store[key]
    
    def clear(self) -> None:
        """Clear all keys (useful for testing)."""
        self._store.clear()


class SQLiteKVCache(KVCache):
    """SQLite-based persistent cache (for local development)."""
    
    def __init__(self, db_path: str = "cache.db"):
        """
        Initialize SQLite cache.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_db()
        logger.info(f"SQLiteKVCache initialized: {db_path}")
    
    def _init_db(self) -> None:
        """Create cache table if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kv_cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                expiry TIMESTAMP NULL
            )
        ''')
        conn.commit()
        conn.close()
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a key-value pair with optional TTL in seconds."""
        serialized = json.dumps(value)
        expiry = None
        if ttl:
            expiry = (datetime.utcnow() + timedelta(seconds=ttl)).isoformat()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO kv_cache (key, value, expiry)
            VALUES (?, ?, ?)
        ''', (key, serialized, expiry))
        conn.commit()
        conn.close()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key, returns None if not found or expired."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT value, expiry FROM kv_cache WHERE key = ?
        ''', (key,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        value_str, expiry_str = row
        
        # Check if expired
        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str)
            if datetime.utcnow() > expiry:
                self.delete(key)
                return None
        
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            logger.error(f"JSON decode error for key {key}")
            return None
    
    def delete(self, key: str) -> None:
        """Delete a key."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM kv_cache WHERE key = ?', (key,))
        conn.commit()
        conn.close()
    
    def cleanup_expired(self) -> int:
        """Remove all expired keys, returns count of deleted keys."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            DELETE FROM kv_cache
            WHERE expiry IS NOT NULL AND expiry < ?
        ''', (datetime.utcnow().isoformat(),))
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        return deleted


def get_kv_cache() -> KVCache:
    """
    Get KV cache instance based on environment configuration.
    
    Environment variables:
    - KV_CACHE_TYPE: redis, sqlite, or memory (default: memory)
    - REDIS_URL: Redis connection URL (for redis type)
    - CACHE_DB_PATH: SQLite database path (for sqlite type)
    
    Returns:
        KVCache implementation instance
    """
    cache_type = os.getenv("KV_CACHE_TYPE", "memory").lower()
    
    if cache_type == "redis":
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        # Parse Redis URL
        from urllib.parse import urlparse
        parsed = urlparse(redis_url)
        return RedisKVCache(
            host=parsed.hostname or "localhost",
            port=parsed.port or 6379,
            db=int(parsed.path.lstrip("/") or "0"),
        )
    
    elif cache_type == "sqlite":
        db_path = os.getenv("CACHE_DB_PATH", "cache.db")
        return SQLiteKVCache(db_path=db_path)
    
    else:  # memory (default)
        return InMemoryKVCache()

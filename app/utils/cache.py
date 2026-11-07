import redis
import json
from app.config import settings

# Cadangan kalau Redis mati
_memory_cache = {}

try:
    r = redis.from_url(settings.redis_url, decode_responses=True)
    r.ping()
    REDIS_AVAILABLE = True
    print("✅ Redis Connected")
except Exception:
    REDIS_AVAILABLE = False
    print("⚠️ Redis not found. Using in-memory cache (lokal aja).")

def get_cache(key: str):
    if REDIS_AVAILABLE:
        try: return r.get(key)
        except: pass
    return _memory_cache.get(key)

def set_cache(key: str, value: str, ttl: int = 3600):
    if REDIS_AVAILABLE:
        try:
            r.setex(key, ttl, value)
            return
        except: pass
    _memory_cache[key] = value
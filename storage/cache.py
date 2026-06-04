
# storage/cache.py
import threading
import time
from typing import Any, Optional

class TTLCache:
    """
    Dictionary backed store where every value has an expiry time.
    """
    
    def __init__(self) -> None:
        # The actual data: key → (value, expiry_timestamp)
        self._store: dict[str, tuple[Any, float]] = {}
        self._lock = threading.RLock()   # Thread lock to prevent race conditions in concurrent requests

    # Public interface

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
         #Store a value with a time limit (TTL = time to live)
        expiry = time.time() + ttl_seconds # Calculate expiry timestamp 

        with self._lock:
            self._store[key] = (value, expiry) 

    def get(self, key: str) -> Optional[Any]:
        #get value if key exists and hasn't expired
        with self._lock:
            entry = self._store.get(key)

            if entry is None:
                return None  # Key was never set

            value, expiry = entry

            if time.time() > expiry:
                del self._store[key]
                return None

            return value #if valid return stored value

    def delete(self, key: str) -> bool:
       
        #Manually remove a key before its TTL expires.

        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def evict_expired(self) -> int:
        #Remove all expired entries from the cache.
        now = time.time()
        evicted = 0

        with self._lock:
            # Build the list of expired keys first 
            expired_keys = [
                key
                for key, (_, expiry) in self._store.items()
                if now > expiry
            ]
            for key in expired_keys:
                del self._store[key]
                evicted += 1

        return evicted

    def size(self) -> int:
        #Number of unexpired entries currently in the cache.
        
        self.evict_expired()

        with self._lock:
            return len(self._store)

# ensures everyone is looking at the same data.
event_cache = TTLCache()

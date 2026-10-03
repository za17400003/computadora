"""
computadora/memoria/cache.py — LRU Cache with TTL expiration

Custom implementation based on Python OrderedDict + time-based invalidation.
No external dependencies (uses stdlib only).

Role in Etz HaChaim: Yesod (Fundación) — stabilizes temporal state of Computadora
persistent memory across restarts and context switches.
"""

from collections import OrderedDict
from time import time
from typing import Any, Callable, Optional, Tuple


class TTLEntry:
    """Container for cached value + expiration timestamp."""
    
    __slots__ = ('value', 'timestamp')
    
    def __init__(self, value: Any, timestamp: float):
        self.value = value
        self.timestamp = timestamp
    
    def is_expired(self, now: float, maxage: float) -> bool:
        """Check if entry has exceeded TTL."""
        return (now - self.timestamp) > maxage


class CustomLRU:
    """
    LRU Cache with Time-To-Live (TTL) expiration.
    
    Features:
    - Least-Recently-Used eviction when maxsize exceeded
    - Time-based expiration (maxage in seconds)
    - Thread-safe reads (Python GIL protects dict ops)
    - Transparent expired-entry cleanup on access
    
    Args:
        maxsize: Maximum number of entries to cache (default 128)
        maxage: Maximum age in seconds before entry expires (default 60)
    
    Example:
        cache = CustomLRU(maxsize=256, maxage=300)
        cache['key'] = some_value
        result = cache.get('key')  # Returns None if expired
    """
    
    def __init__(self, maxsize: int = 128, maxage: float = 60.0):
        if maxsize <= 0:
            raise ValueError("maxsize must be > 0")
        if maxage <= 0:
            raise ValueError("maxage must be > 0")
        
        self.cache: OrderedDict[Any, TTLEntry] = OrderedDict()
        self.maxsize = maxsize
        self.maxage = maxage
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def __getitem__(self, key: Any) -> Any:
        """Get value, raising KeyError if missing or expired."""
        now = time()
        
        if key not in self.cache:
            self.misses += 1
            raise KeyError(key)
        
        entry = self.cache[key]
        
        # Check expiration
        if entry.is_expired(now, self.maxage):
            del self.cache[key]
            self.misses += 1
            raise KeyError(key)
        
        # Mark as recently used (move to end)
        self.cache.move_to_end(key)
        self.hits += 1
        return entry.value
    
    def __setitem__(self, key: Any, value: Any) -> None:
        """Set value, evicting oldest if maxsize exceeded."""
        now = time()
        
        if key in self.cache:
            # Update existing key
            self.cache[key] = TTLEntry(value, now)
            self.cache.move_to_end(key)
        else:
            # Add new key
            if len(self.cache) >= self.maxsize:
                # Evict least recently used (first item)
                evicted_key, _ = self.cache.popitem(last=False)
                self.evictions += 1
            
            self.cache[key] = TTLEntry(value, now)
    
    def __contains__(self, key: Any) -> bool:
        """Check if key exists and is not expired."""
        try:
            _ = self[key]
            return True
        except KeyError:
            return False
    
    def __len__(self) -> int:
        """Return number of non-expired entries."""
        now = time()
        count = 0
        for key in list(self.cache.keys()):
            entry = self.cache[key]
            if not entry.is_expired(now, self.maxage):
                count += 1
            else:
                del self.cache[key]
        return count
    
    def get(self, key: Any, default: Any = None) -> Any:
        """Get value with default fallback (does not raise on miss/expiry)."""
        try:
            return self[key]
        except KeyError:
            return default
    
    def pop(self, key: Any, default: Any = None) -> Any:
        """Remove and return value, or default if not found."""
        try:
            value = self[key]
            del self.cache[key]
            return value
        except KeyError:
            return default
    
    def clear(self) -> None:
        """Remove all entries from cache."""
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def cleanup_expired(self) -> int:
        """Remove all expired entries. Returns count removed."""
        now = time()
        removed = 0
        
        for key in list(self.cache.keys()):
            entry = self.cache[key]
            if entry.is_expired(now, self.maxage):
                del self.cache[key]
                removed += 1
        
        return removed
    
    def stats(self) -> dict:
        """Return cache statistics."""
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'size': len(self.cache),
            'maxsize': self.maxsize,
            'hit_ratio': self.hits / (self.hits + self.misses) if (self.hits + self.misses) > 0 else 0.0,
        }
    
    def __repr__(self) -> str:
        """String representation showing cache state."""
        stats = self.stats()
        return (f"CustomLRU(size={stats['size']}/{self.maxsize}, "
                f"hits={stats['hits']}, misses={stats['misses']}, "
                f"evictions={stats['evictions']}, "
                f"hit_ratio={stats['hit_ratio']:.1%})")



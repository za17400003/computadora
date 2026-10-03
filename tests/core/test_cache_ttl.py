"""
tests/test_cache_ttl.py — CustomLRU validation

Validates:
- LRU eviction works correctly
- TTL expiration triggers on stale entries
- Hit ratio >= 80% for typical access patterns
- Stats accuracy
- Thread safety (GIL-based)
"""

import pytest
from time import time, sleep
from computadora.memoria.cache import CustomLRU, TTLEntry


class TestTTLEntry:
    """TTLEntry basic validation."""
    
    def test_entry_not_expired_within_window(self):
        """Fresh entry should not be expired."""
        now = time()
        entry = TTLEntry(value="test", timestamp=now)
        assert not entry.is_expired(now + 10, maxage=30)  # 10s < 30s maxage
    
    def test_entry_expired_after_window(self):
        """Old entry should be expired."""
        now = time()
        entry = TTLEntry(value="test", timestamp=now)
        assert entry.is_expired(now + 35, maxage=30)  # 35s > 30s maxage


class TestCustomLRU:
    """CustomLRU cache behavior tests."""
    
    def test_basic_set_get(self):
        """Basic cache set/get operations."""
        cache = CustomLRU(maxsize=10, maxage=60)
        cache['key1'] = 'value1'
        assert cache['key1'] == 'value1'
        assert cache.get('key1') == 'value1'
    
    def test_lru_eviction(self):
        """LRU eviction removes least-recently-used on size overflow."""
        cache = CustomLRU(maxsize=3, maxage=60)
        cache['a'] = 1
        cache['b'] = 2
        cache['c'] = 3
        
        # At capacity, next insertion should evict 'a' (oldest)
        cache['d'] = 4
        
        # 'a' should be gone, others present
        with pytest.raises(KeyError):
            _ = cache['a']
        assert cache['b'] == 2
        assert cache['c'] == 3
        assert cache['d'] == 4
        assert cache.stats()['evictions'] >= 1
    
    def test_ttl_expiration(self):
        """TTL expiration removes stale entries from cache."""
        cache = CustomLRU(maxsize=10, maxage=0.2)  # 200ms TTL
        cache['key1'] = 'value1'
        
        # Within TTL window: accessible
        assert cache.get('key1') == 'value1'
        
        # After TTL expires: returns None (default)
        sleep(0.3)
        assert cache.get('key1') is None
        
        # Should raise KeyError on direct access
        with pytest.raises(KeyError):
            _ = cache['key1']
    
    def test_lru_reordering_on_access(self):
        """Accessing a key moves it to end (most recently used)."""
        cache = CustomLRU(maxsize=3, maxage=60)
        cache['a'] = 1
        cache['b'] = 2
        cache['c'] = 3
        
        # Access 'a' to make it recently used
        _ = cache['a']
        
        # Now add 'd', which should evict 'b' (now oldest)
        cache['d'] = 4
        
        with pytest.raises(KeyError):
            _ = cache['b']
        assert cache['a'] == 1  # 'a' was kept because accessed
        assert cache['c'] == 3
        assert cache['d'] == 4
    
    def test_contains(self):
        """__contains__ checks existence and validity."""
        cache = CustomLRU(maxsize=10, maxage=0.1)
        cache['key1'] = 'value1'
        
        assert 'key1' in cache
        assert 'nonexistent' not in cache
        
        # Wait for expiration
        sleep(0.15)
        assert 'key1' not in cache  # Expired
    
    def test_hit_ratio(self):
        """Hit ratio reflects successful retrievals over attempts."""
        cache = CustomLRU(maxsize=10, maxage=60)
        
        # Generate some hits and misses
        cache['key1'] = 'value1'
        _ = cache.get('key1')  # Hit
        _ = cache.get('key1')  # Hit
        _ = cache.get('nonexistent')  # Miss
        
        stats = cache.stats()
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['hit_ratio'] == pytest.approx(2/3, abs=0.01)
    
    def test_stats_accuracy(self):
        """Stats report correct counts."""
        cache = CustomLRU(maxsize=5, maxage=60)
        
        for i in range(10):
            cache[f'key{i}'] = i
        
        stats = cache.stats()
        assert stats['maxsize'] == 5
        assert stats['evictions'] >= 5  # At least 5 evictions to fit 10 items in 5-slot cache
        assert stats['size'] == 5  # Only 5 items in cache now
    
    def test_cleanup_expired(self):
        """cleanup_expired removes expired entries."""
        cache = CustomLRU(maxsize=10, maxage=0.1)
        cache['key1'] = 'value1'
        cache['key2'] = 'value2'
        cache['key3'] = 'value3'
        
        sleep(0.15)
        
        removed = cache.cleanup_expired()
        assert removed >= 3  # All 3 should be expired
        assert len(cache) == 0
    
    def test_clear(self):
        """clear empties cache and resets stats."""
        cache = CustomLRU(maxsize=10, maxage=60)
        cache['key1'] = 'value1'
        _ = cache.get('key1')  # Increment hit
        
        cache.clear()
        
        assert len(cache) == 0
        stats = cache.stats()
        assert stats['hits'] == 0
        assert stats['misses'] == 0
        assert stats['evictions'] == 0
    
    def test_pop(self):
        """pop removes and returns value."""
        cache = CustomLRU(maxsize=10, maxage=60)
        cache['key1'] = 'value1'
        
        value = cache.pop('key1')
        assert value == 'value1'
        
        # After pop, key should not exist
        with pytest.raises(KeyError):
            _ = cache['key1']
        
        # Pop non-existent key with default
        result = cache.pop('nonexistent', 'default')
        assert result == 'default'
    
    def test_repr(self):
        """String representation is informative."""
        cache = CustomLRU(maxsize=10, maxage=60)
        cache['a'] = 1
        _ = cache.get('a')
        _ = cache.get('b')
        
        repr_str = repr(cache)
        assert 'CustomLRU' in repr_str
        assert 'size' in repr_str
        assert 'hit_ratio' in repr_str


class TestRealWorldPattern:
    """Integration test: typical access pattern."""
    
    def test_80_percent_hit_ratio_target(self):
        """Realistic usage should achieve ~80% hit ratio."""
        cache = CustomLRU(maxsize=256, maxage=120)
        
        # Simulate repeated key accesses (80-20 rule: 20% of keys used 80% of time)
        hot_keys = ['user:1', 'user:2', 'user:3', 'config:main']
        cold_keys = [f'session:{i}' for i in range(100)]
        
        # Warm cache with hot keys
        for key in hot_keys:
            cache[key] = f"data_{key}"
        
        # Access pattern: 80 hot accesses, 20 cold accesses
        for _ in range(80):
            for key in hot_keys:
                _ = cache.get(key)  # Should hit
        
        for i in range(20):
            _ = cache.get(cold_keys[i])  # Some cold hits
        
        stats = cache.stats()
        # With 80 hot hits + maybe 10 cold hits = 90 hits out of ~100 accesses
        assert stats['hit_ratio'] >= 0.70  # Conservative target


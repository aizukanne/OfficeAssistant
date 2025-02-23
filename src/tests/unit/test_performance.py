import pytest
import time
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock
from src.core.performance import (
    LRUCache,
    ConnectionPool,
    RequestQueue,
    PerformanceMonitor,
    cached,
    monitor_performance
)
from src.core.exceptions import TimeoutError

@pytest.fixture
def lru_cache():
    """Create LRUCache instance."""
    return LRUCache(capacity=3, ttl=1)

@pytest.fixture
def performance_monitor():
    """Create PerformanceMonitor instance."""
    return PerformanceMonitor()

def test_lru_cache_put_get(lru_cache):
    """Test basic cache put and get operations."""
    lru_cache.put('key1', 'value1')
    assert lru_cache.get('key1') == 'value1'
    assert lru_cache.get('nonexistent') is None

def test_lru_cache_capacity(lru_cache):
    """Test cache capacity limit."""
    lru_cache.put('key1', 'value1')
    lru_cache.put('key2', 'value2')
    lru_cache.put('key3', 'value3')
    lru_cache.put('key4', 'value4')  # Should evict key1
    
    assert lru_cache.get('key1') is None
    assert lru_cache.get('key2') == 'value2'
    assert lru_cache.get('key3') == 'value3'
    assert lru_cache.get('key4') == 'value4'

def test_lru_cache_ttl(lru_cache):
    """Test cache TTL expiration."""
    lru_cache.put('key1', 'value1')
    assert lru_cache.get('key1') == 'value1'
    
    time.sleep(1.1)  # Wait for TTL to expire
    assert lru_cache.get('key1') is None

def test_lru_cache_update_existing(lru_cache):
    """Test updating existing cache entry."""
    lru_cache.put('key1', 'value1')
    lru_cache.put('key1', 'value2')
    assert lru_cache.get('key1') == 'value2'

def test_lru_cache_clear(lru_cache):
    """Test cache clearing."""
    lru_cache.put('key1', 'value1')
    lru_cache.put('key2', 'value2')
    lru_cache.clear()
    assert lru_cache.get('key1') is None
    assert lru_cache.get('key2') is None

@pytest.mark.asyncio
async def test_connection_pool_get_connection():
    """Test getting connection from pool."""
    mock_connection = MagicMock()
    create_connection = MagicMock(return_value=mock_connection)
    
    pool = ConnectionPool(create_connection, max_size=2)
    conn = await pool.get_connection()
    
    assert conn == mock_connection
    assert pool.size == 1

@pytest.mark.asyncio
async def test_connection_pool_max_size():
    """Test connection pool maximum size."""
    mock_connection = MagicMock()
    create_connection = MagicMock(return_value=mock_connection)
    
    pool = ConnectionPool(create_connection, max_size=1, timeout=1)
    
    # Get first connection
    conn1 = await pool.get_connection()
    
    # Second connection should timeout
    with pytest.raises(TimeoutError):
        await pool.get_connection()

@pytest.mark.asyncio
async def test_connection_pool_release():
    """Test releasing connection back to pool."""
    mock_connection = MagicMock()
    create_connection = MagicMock(return_value=mock_connection)
    
    pool = ConnectionPool(create_connection, max_size=1)
    
    conn = await pool.get_connection()
    await pool.release_connection(conn)
    
    # Should be able to get the connection again
    conn2 = await pool.get_connection()
    assert conn2 == mock_connection

@pytest.mark.asyncio
async def test_request_queue_priority():
    """Test request queue priority ordering."""
    queue = RequestQueue()
    
    # Add requests with different priorities
    await queue.enqueue({'id': 1}, 'low')
    await queue.enqueue({'id': 2}, 'normal')
    await queue.enqueue({'id': 3}, 'high')
    
    # Should get high priority first
    request = await queue.dequeue()
    assert request['id'] == 3
    
    # Then normal priority
    request = await queue.dequeue()
    assert request['id'] == 2
    
    # Then low priority
    request = await queue.dequeue()
    assert request['id'] == 1

@pytest.mark.asyncio
async def test_request_queue_empty():
    """Test empty request queue."""
    queue = RequestQueue()
    assert await queue.dequeue() is None

def test_performance_monitor_record_metric(performance_monitor):
    """Test recording performance metrics."""
    performance_monitor.record_metric('test_metric', 100, 'timing')
    metrics = performance_monitor.get_metrics()
    
    assert 'test_metric' in metrics
    assert metrics['test_metric']['count'] == 1
    assert metrics['test_metric']['total'] == 100
    assert metrics['test_metric']['min'] == 100
    assert metrics['test_metric']['max'] == 100

def test_performance_monitor_multiple_records(performance_monitor):
    """Test recording multiple metrics."""
    performance_monitor.record_metric('test_metric', 100)
    performance_monitor.record_metric('test_metric', 200)
    
    metrics = performance_monitor.get_metrics()
    assert metrics['test_metric']['count'] == 2
    assert metrics['test_metric']['total'] == 300
    assert metrics['test_metric']['min'] == 100
    assert metrics['test_metric']['max'] == 200

def test_cached_decorator():
    """Test cached decorator."""
    call_count = 0
    
    @cached()
    def test_function(arg):
        nonlocal call_count
        call_count += 1
        return f"result_{arg}"
    
    # First call should execute function
    result1 = test_function("test")
    assert result1 == "result_test"
    assert call_count == 1
    
    # Second call should use cache
    result2 = test_function("test")
    assert result2 == "result_test"
    assert call_count == 1  # Shouldn't have incremented

def test_monitor_performance_decorator():
    """Test performance monitoring decorator."""
    monitor = PerformanceMonitor()
    
    @monitor_performance("test_function")
    def test_function():
        time.sleep(0.1)
        return "result"
    
    with patch('src.core.performance.performance_monitor', monitor):
        result = test_function()
        
        metrics = monitor.get_metrics()
        assert "test_function" in metrics
        assert metrics["test_function"]["count"] == 1
        assert metrics["test_function"]["total"] >= 0.1

def test_monitor_performance_error():
    """Test performance monitoring with error."""
    monitor = PerformanceMonitor()
    
    @monitor_performance("test_function")
    def test_function():
        time.sleep(0.1)
        raise ValueError("test error")
    
    with patch('src.core.performance.performance_monitor', monitor):
        with pytest.raises(ValueError):
            test_function()
        
        metrics = monitor.get_metrics()
        assert "test_function_error" in metrics
        assert metrics["test_function_error"]["count"] == 1

@pytest.mark.asyncio
async def test_connection_pool_concurrent_access():
    """Test connection pool under concurrent access."""
    mock_connection = MagicMock()
    create_connection = MagicMock(return_value=mock_connection)
    
    pool = ConnectionPool(create_connection, max_size=5)
    
    async def worker():
        conn = await pool.get_connection()
        await asyncio.sleep(0.1)  # Simulate work
        await pool.release_connection(conn)
    
    # Create multiple concurrent workers
    workers = [worker() for _ in range(10)]
    await asyncio.gather(*workers)
    
    # Pool size should not have exceeded max_size
    assert pool.size <= 5

def test_lru_cache_thread_safety():
    """Test LRU cache thread safety."""
    cache = LRUCache(capacity=100)
    success_count = 0
    thread_count = 100
    
    def worker():
        nonlocal success_count
        try:
            cache.put(f"key_{time.time()}", "value")
            success_count += 1
        except Exception:
            pass
    
    threads = [
        threading.Thread(target=worker)
        for _ in range(thread_count)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    assert success_count == thread_count
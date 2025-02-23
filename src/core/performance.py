import time
import asyncio
import threading
from typing import Dict, Any, Optional, Callable, TypeVar, Union
from functools import wraps
from datetime import datetime, timedelta
from collections import OrderedDict

from src.core.exceptions import TimeoutError
from src.core.logging import ServiceLogger

# Initialize logger
logger = ServiceLogger('performance')

T = TypeVar('T')

class LRUCache:
    """Least Recently Used (LRU) cache implementation."""
    
    def __init__(self, capacity: int, ttl: int = 300):
        """
        Initialize LRU cache.
        
        Args:
            capacity: Maximum number of items to store
            ttl: Time to live in seconds (default: 5 minutes)
        """
        self.capacity = capacity
        self.ttl = ttl
        self.cache: OrderedDict = OrderedDict()
        self.timestamps: Dict[str, float] = {}
        self.lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get item from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Optional[Any]: Cached value if exists and not expired
        """
        with self.lock:
            if key not in self.cache:
                return None
            
            # Check if expired
            if time.time() - self.timestamps[key] > self.ttl:
                self.cache.pop(key)
                self.timestamps.pop(key)
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            return self.cache[key]
    
    def put(self, key: str, value: Any) -> None:
        """
        Put item in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        with self.lock:
            if key in self.cache:
                # Move to end and update
                self.cache.move_to_end(key)
            else:
                # Check capacity
                if len(self.cache) >= self.capacity:
                    # Remove least recently used
                    oldest_key, _ = self.cache.popitem(last=False)
                    self.timestamps.pop(oldest_key)
            
            self.cache[key] = value
            self.timestamps[key] = time.time()
    
    def clear(self) -> None:
        """Clear the cache."""
        with self.lock:
            self.cache.clear()
            self.timestamps.clear()

class ConnectionPool:
    """Generic connection pool implementation."""
    
    def __init__(
        self,
        create_connection: Callable[[], T],
        max_size: int = 10,
        timeout: int = 30
    ):
        """
        Initialize connection pool.
        
        Args:
            create_connection: Function to create new connections
            max_size: Maximum pool size
            timeout: Connection timeout in seconds
        """
        self.create_connection = create_connection
        self.max_size = max_size
        self.timeout = timeout
        self.pool: asyncio.Queue[T] = asyncio.Queue(maxsize=max_size)
        self.size = 0
        self.lock = asyncio.Lock()
    
    async def get_connection(self) -> T:
        """
        Get a connection from the pool.
        
        Returns:
            T: Connection object
            
        Raises:
            TimeoutError: If no connection available within timeout
        """
        try:
            # Try to get existing connection
            return await asyncio.wait_for(self.pool.get(), self.timeout)
        except asyncio.TimeoutError:
            # Create new connection if pool not full
            async with self.lock:
                if self.size < self.max_size:
                    self.size += 1
                    return self.create_connection()
            
            # Pool is full, wait for connection
            try:
                return await asyncio.wait_for(self.pool.get(), self.timeout)
            except asyncio.TimeoutError:
                raise TimeoutError("Connection pool timeout")
    
    async def release_connection(self, connection: T) -> None:
        """
        Release connection back to pool.
        
        Args:
            connection: Connection to release
        """
        await self.pool.put(connection)

class RequestQueue:
    """Request queue with prioritization."""
    
    def __init__(self, max_size: int = 1000):
        """
        Initialize request queue.
        
        Args:
            max_size: Maximum queue size
        """
        self.max_size = max_size
        self.high_priority: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.normal_priority: asyncio.Queue = asyncio.Queue(maxsize=max_size)
        self.low_priority: asyncio.Queue = asyncio.Queue(maxsize=max_size)
    
    async def enqueue(
        self,
        request: Dict[str, Any],
        priority: str = 'normal'
    ) -> None:
        """
        Enqueue a request.
        
        Args:
            request: Request to enqueue
            priority: Priority level ('high', 'normal', 'low')
        """
        if priority == 'high':
            await self.high_priority.put(request)
        elif priority == 'low':
            await self.low_priority.put(request)
        else:
            await self.normal_priority.put(request)
    
    async def dequeue(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue next request based on priority.
        
        Returns:
            Optional[Dict[str, Any]]: Next request or None if all queues empty
        """
        # Try high priority first
        try:
            return await self.high_priority.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try normal priority
        try:
            return await self.normal_priority.get_nowait()
        except asyncio.QueueEmpty:
            pass
        
        # Try low priority
        try:
            return await self.low_priority.get_nowait()
        except asyncio.QueueEmpty:
            return None

class PerformanceMonitor:
    """Performance monitoring implementation."""
    
    def __init__(self):
        """Initialize performance monitor."""
        self.logger = ServiceLogger('performance_monitor')
        self.metrics: Dict[str, Dict[str, Union[int, float]]] = {}
        self.lock = threading.Lock()
    
    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: str = 'timing'
    ) -> None:
        """
        Record a performance metric.
        
        Args:
            name: Metric name
            value: Metric value
            metric_type: Type of metric ('timing', 'count', etc.)
        """
        with self.lock:
            if name not in self.metrics:
                self.metrics[name] = {
                    'count': 0,
                    'total': 0.0,
                    'min': float('inf'),
                    'max': float('-inf'),
                    'type': metric_type
                }
            
            metric = self.metrics[name]
            metric['count'] += 1
            metric['total'] += value
            metric['min'] = min(metric['min'], value)
            metric['max'] = max(metric['max'], value)
            
            # Log if significant change
            avg = metric['total'] / metric['count']
            if value > avg * 2:  # More than double average
                self.logger.warning(
                    f"High {metric_type} detected",
                    metric=name,
                    value=value,
                    average=avg
                )
    
    def get_metrics(self) -> Dict[str, Dict[str, Union[int, float]]]:
        """
        Get current metrics.
        
        Returns:
            Dict[str, Dict[str, Union[int, float]]]: Current metrics
        """
        with self.lock:
            return self.metrics.copy()

# Global instances
cache = LRUCache(1000)  # 1000 items, 5 minutes TTL
request_queue = RequestQueue()
performance_monitor = PerformanceMonitor()

def cached(ttl: Optional[int] = None):
    """
    Caching decorator.
    
    Args:
        ttl: Optional custom TTL in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            result = cache.get(key)
            if result is not None:
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.put(key, result)
            return result
        return wrapper
    return decorator

def monitor_performance(metric_name: str):
    """
    Performance monitoring decorator.
    
    Args:
        metric_name: Name of the metric to record
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    metric_name,
                    duration,
                    'timing'
                )
                return result
            except Exception as e:
                duration = time.time() - start_time
                performance_monitor.record_metric(
                    f"{metric_name}_error",
                    duration,
                    'error'
                )
                raise
        return wrapper
    return decorator
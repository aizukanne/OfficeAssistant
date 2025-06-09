"""
Connection pooling implementation for Weaviate to improve performance
and resource utilization in parallel operations.
"""

import weaviate
import threading
import queue
import time
from contextlib import contextmanager
from typing import Optional, Dict, Any
from weaviate.classes.init import Auth
from parallel_utils import time_operation_with_metrics


class WeaviateConnectionPool:
    """
    Thread-safe connection pool for Weaviate clients.
    Manages a pool of connections to avoid connection overhead in parallel operations.
    """
    
    def __init__(self, cluster_url: str, api_key: str, headers: Dict[str, str], 
                 pool_size: int = 5, max_overflow: int = 2, timeout: float = 30.0):
        """
        Initialize the connection pool.
        
        Args:
            cluster_url: Weaviate cluster URL
            api_key: API key for authentication
            headers: Additional headers for requests
            pool_size: Number of connections to maintain in the pool
            max_overflow: Maximum number of overflow connections allowed
            timeout: Timeout for getting a connection from the pool
        """
        self.cluster_url = cluster_url
        self.api_key = api_key
        self.headers = headers
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.timeout = timeout
        
        # Thread-safe queue for available connections
        self.pool = queue.Queue(maxsize=pool_size + max_overflow)
        self.lock = threading.Lock()
        self.created_connections = 0
        self.active_connections = 0
        
        # Statistics - Initialize before pool creation
        self.stats = {
            'connections_created': 0,
            'connections_reused': 0,
            'connection_errors': 0,
            'pool_exhausted_count': 0
        }
        
        # Initialize the pool with connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the pool with the specified number of connections."""
        for _ in range(self.pool_size):
            try:
                client = self._create_connection()
                self.pool.put(client)
            except Exception as e:
                print(f"Error creating initial connection: {e}")
    
    def _create_connection(self) -> weaviate.Client:
        """Create a new Weaviate client connection."""
        with self.lock:
            self.created_connections += 1
            self.stats['connections_created'] += 1
        
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.cluster_url,
            auth_credentials=Auth.api_key(self.api_key),
            headers=self.headers
        )
        return client
    
    @contextmanager
    @time_operation_with_metrics("weaviate_connection_pool_get")
    def get_client(self):
        """
        Get a client from the pool. This is a context manager that ensures
        the connection is returned to the pool after use.
        
        Yields:
            weaviate.Client: A Weaviate client connection
            
        Raises:
            TimeoutError: If unable to get a connection within the timeout period
        """
        client = None
        acquired = False
        
        try:
            # Try to get a connection from the pool
            try:
                client = self.pool.get(timeout=self.timeout)
                acquired = True
                with self.lock:
                    self.active_connections += 1
                    self.stats['connections_reused'] += 1
            except queue.Empty:
                # Pool is empty, try to create overflow connection
                with self.lock:
                    if self.created_connections < self.pool_size + self.max_overflow:
                        client = self._create_connection()
                        acquired = True
                        self.active_connections += 1
                    else:
                        self.stats['pool_exhausted_count'] += 1
                        raise TimeoutError(f"Connection pool exhausted (timeout: {self.timeout}s)")
            
            # Verify connection is still valid
            if client and not self._is_connection_valid(client):
                client.close()
                client = self._create_connection()
            
            yield client
            
        except Exception as e:
            with self.lock:
                self.stats['connection_errors'] += 1
            raise e
        finally:
            # Return connection to pool
            if client and acquired:
                with self.lock:
                    self.active_connections -= 1
                
                # Only return to pool if under pool size limit
                if self.pool.qsize() < self.pool_size:
                    self.pool.put(client)
                else:
                    # Close overflow connection
                    try:
                        client.close()
                    except:
                        pass
                    with self.lock:
                        self.created_connections -= 1
    
    def _is_connection_valid(self, client: weaviate.Client) -> bool:
        """
        Check if a connection is still valid.
        
        Args:
            client: The Weaviate client to check
            
        Returns:
            bool: True if connection is valid, False otherwise
        """
        try:
            # Simple health check - adjust based on Weaviate client capabilities
            client.is_ready()
            return True
        except:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get pool statistics."""
        with self.lock:
            return {
                **self.stats,
                'pool_size': self.pool_size,
                'max_overflow': self.max_overflow,
                'current_pool_size': self.pool.qsize(),
                'active_connections': self.active_connections,
                'total_created': self.created_connections
            }
    
    def close_all(self):
        """Close all connections in the pool."""
        while not self.pool.empty():
            try:
                client = self.pool.get_nowait()
                client.close()
            except queue.Empty:
                break
            except Exception as e:
                print(f"Error closing connection: {e}")
        
        with self.lock:
            self.created_connections = 0
            self.active_connections = 0


# Singleton instance management
_pool_instance: Optional[WeaviateConnectionPool] = None
_pool_lock = threading.Lock()


def get_weaviate_pool(cluster_url: str, api_key: str, headers: Dict[str, str],
                      pool_size: int = 5, max_overflow: int = 2) -> WeaviateConnectionPool:
    """
    Get or create the singleton Weaviate connection pool.
    
    Args:
        cluster_url: Weaviate cluster URL
        api_key: API key for authentication
        headers: Additional headers
        pool_size: Size of the connection pool
        max_overflow: Maximum overflow connections
        
    Returns:
        WeaviateConnectionPool: The connection pool instance
    """
    global _pool_instance
    
    with _pool_lock:
        if _pool_instance is None:
            _pool_instance = WeaviateConnectionPool(
                cluster_url=cluster_url,
                api_key=api_key,
                headers=headers,
                pool_size=pool_size,
                max_overflow=max_overflow
            )
    
    return _pool_instance


def close_weaviate_pool():
    """Close the singleton Weaviate connection pool."""
    global _pool_instance
    
    with _pool_lock:
        if _pool_instance:
            _pool_instance.close_all()
            _pool_instance = None
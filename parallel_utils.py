"""
Parallelization utilities for Lambda function performance optimization.
This module provides timing decorators and parallel execution capabilities.
"""

import time
import json
import boto3
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import List, Tuple, Dict, Any, Callable, Optional


# Initialize CloudWatch client for metrics
try:
    cloudwatch = boto3.client('cloudwatch')
except Exception as e:
    print(f"Warning: Could not initialize CloudWatch client: {e}")
    cloudwatch = None


def time_operation(operation_name: str) -> Callable:
    """
    Decorator to time function execution and log the duration.
    
    Args:
        operation_name: Name of the operation for logging
        
    Returns:
        Decorated function that logs execution time
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            duration = end_time - start_time
            print(f"[TIMING] {operation_name}: {duration:.3f}s")
            return result
        return wrapper
    return decorator


def time_operation_with_metrics(operation_name: str, namespace: str = 'OfficeAssistant') -> Callable:
    """
    Enhanced timing decorator that sends metrics to CloudWatch.
    
    Args:
        operation_name: Name of the operation for logging and metrics
        namespace: CloudWatch namespace for metrics
        
    Returns:
        Decorated function that logs execution time and sends metrics
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            print(f"[TIMING] {operation_name}: {duration:.1f}ms")
            
            # Send metric to CloudWatch if available
            if cloudwatch:
                send_metric(f"{operation_name}_duration", duration, 'Milliseconds', namespace)
            
            return result
        return wrapper
    return decorator


def send_metric(metric_name: str, value: float, unit: str = 'Milliseconds', 
                namespace: str = 'OfficeAssistant') -> None:
    """
    Send custom metric to CloudWatch.
    
    Args:
        metric_name: Name of the metric
        value: Metric value
        unit: Unit of measurement
        namespace: CloudWatch namespace
    """
    if not cloudwatch:
        return
        
    try:
        cloudwatch.put_metric_data(
            Namespace=namespace,
            MetricData=[
                {
                    'MetricName': metric_name,
                    'Value': value,
                    'Unit': unit,
                    'Timestamp': datetime.utcnow()
                }
            ]
        )
    except Exception as e:
        print(f"Failed to send metric {metric_name}: {e}")


def log_performance_data(operation: str, duration: float, metadata: Optional[Dict] = None) -> None:
    """
    Log performance data in structured format for CloudWatch Insights.
    
    Args:
        operation: Name of the operation
        duration: Duration in milliseconds
        metadata: Additional metadata to log
    """
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "operation": operation,
        "duration_ms": duration,
        "metadata": metadata or {}
    }
    print(json.dumps(log_entry))


class ParallelExecutor:
    """
    Manages parallel execution of multiple tasks using ThreadPoolExecutor.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize the ParallelExecutor.
        
        Args:
            max_workers: Maximum number of worker threads
        """
        self.max_workers = max_workers
    
    def execute_parallel_tasks(self, tasks: List[Tuple[Callable, Tuple, Dict]]) -> Dict[int, Any]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            tasks: List of tuples containing (function, args, kwargs)
            
        Returns:
            Dictionary of results keyed by task index
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(func, *args, **kwargs): idx 
                for idx, (func, args, kwargs) in enumerate(tasks)
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_index):
                idx = future_to_index[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"Task {idx} failed: {e}")
                    results[idx] = None
                    # Log the error for monitoring
                    log_performance_data(
                        f"parallel_task_error",
                        0,
                        {"task_index": idx, "error": str(e)}
                    )
        
        return results
    
    def execute_with_timeout(self, tasks: List[Tuple[Callable, Tuple, Dict]], 
                           timeout: float = 30.0) -> Dict[int, Any]:
        """
        Execute tasks in parallel with a timeout.
        
        Args:
            tasks: List of tuples containing (function, args, kwargs)
            timeout: Maximum time to wait for all tasks to complete
            
        Returns:
            Dictionary of results keyed by task index
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            futures = {}
            for idx, (func, args, kwargs) in enumerate(tasks):
                future = executor.submit(func, *args, **kwargs)
                futures[future] = idx
            
            # Wait for completion with timeout
            completed, pending = concurrent.futures.wait(
                futures.keys(), 
                timeout=timeout,
                return_when=concurrent.futures.ALL_COMPLETED
            )
            
            # Process completed tasks
            for future in completed:
                idx = futures[future]
                try:
                    results[idx] = future.result()
                except Exception as e:
                    print(f"Task {idx} failed: {e}")
                    results[idx] = None
            
            # Cancel pending tasks
            for future in pending:
                idx = futures[future]
                future.cancel()
                print(f"Task {idx} timed out after {timeout}s")
                results[idx] = None
        
        return results


# Utility function for batch processing
def batch_process_parallel(items: List[Any], process_func: Callable, 
                         batch_size: int = 10, max_workers: int = 5) -> List[Any]:
    """
    Process items in parallel batches.
    
    Args:
        items: List of items to process
        process_func: Function to process each item
        batch_size: Number of items per batch
        max_workers: Maximum number of worker threads
        
    Returns:
        List of processed results
    """
    executor = ParallelExecutor(max_workers=max_workers)
    all_results = []
    
    # Process in batches
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        tasks = [(process_func, (item,), {}) for item in batch]
        
        batch_results = executor.execute_parallel_tasks(tasks)
        
        # Collect results in order
        for j in range(len(batch)):
            all_results.append(batch_results.get(j))
    
    return all_results
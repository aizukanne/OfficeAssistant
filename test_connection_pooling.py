"""
Test script to verify Weaviate connection pooling performance improvements.
"""

import time
import json
from typing import List, Dict, Any
from storage import get_last_messages_weaviate, get_relevant_messages
from storage_pooled import (
    init_weaviate_pool, 
    get_last_messages_weaviate_pooled,
    get_relevant_messages_pooled,
    get_pool_statistics
)
from config import user_table, assistant_table


def test_connection_pooling_performance():
    """Compare performance with and without connection pooling."""
    
    print("=" * 60)
    print("WEAVIATE CONNECTION POOLING TEST")
    print("=" * 60)
    
    # Test parameters
    test_chat_id = "test_chat_123"
    num_messages = 10
    test_query = "test query for relevance search"
    num_operations = 5
    
    # Initialize connection pool
    print("\nInitializing connection pool...")
    init_weaviate_pool(pool_size=3, max_overflow=1)
    
    # Test 1: Without pooling (using original functions)
    print("\n1. Testing WITHOUT Connection Pooling")
    print("-" * 40)
    
    start_time = time.time()
    for i in range(num_operations):
        try:
            # Get messages without pooling
            user_msgs = get_last_messages_weaviate(user_table, test_chat_id, num_messages)
            asst_msgs = get_last_messages_weaviate(assistant_table, test_chat_id, num_messages)
            print(f"  Operation {i+1}: Retrieved {len(user_msgs)} user, {len(asst_msgs)} assistant messages")
        except Exception as e:
            print(f"  Operation {i+1} failed: {e}")
    
    no_pool_time = time.time() - start_time
    print(f"\nTotal time without pooling: {no_pool_time:.3f}s")
    print(f"Average per operation: {no_pool_time/num_operations:.3f}s")
    
    # Test 2: With pooling
    print("\n2. Testing WITH Connection Pooling")
    print("-" * 40)
    
    start_time = time.time()
    for i in range(num_operations):
        try:
            # Get messages with pooling
            user_msgs = get_last_messages_weaviate_pooled(user_table, test_chat_id, num_messages)
            asst_msgs = get_last_messages_weaviate_pooled(assistant_table, test_chat_id, num_messages)
            print(f"  Operation {i+1}: Retrieved {len(user_msgs)} user, {len(asst_msgs)} assistant messages")
        except Exception as e:
            print(f"  Operation {i+1} failed: {e}")
    
    pool_time = time.time() - start_time
    print(f"\nTotal time with pooling: {pool_time:.3f}s")
    print(f"Average per operation: {pool_time/num_operations:.3f}s")
    
    # Show pool statistics
    pool_stats = get_pool_statistics()
    print(f"\nPool Statistics: {json.dumps(pool_stats, indent=2)}")
    
    # Calculate improvement
    if no_pool_time > 0 and pool_time > 0:
        improvement = ((no_pool_time - pool_time) / no_pool_time) * 100
        speedup = no_pool_time / pool_time
        print(f"\nPerformance Improvement: {improvement:.1f}%")
        print(f"Speedup: {speedup:.2f}x")
    
    # Test 3: Relevance search comparison
    print("\n3. Testing Relevance Search")
    print("-" * 40)
    
    # Without pooling
    start_time = time.time()
    try:
        rel_user = get_relevant_messages(user_table, test_chat_id, test_query, 5)
        rel_asst = get_relevant_messages(assistant_table, test_chat_id, test_query, 5)
        no_pool_search_time = time.time() - start_time
        print(f"Without pooling: {no_pool_search_time:.3f}s")
    except Exception as e:
        print(f"Without pooling failed: {e}")
        no_pool_search_time = 0
    
    # With pooling
    start_time = time.time()
    try:
        rel_user = get_relevant_messages_pooled(user_table, test_chat_id, test_query, 5)
        rel_asst = get_relevant_messages_pooled(assistant_table, test_chat_id, test_query, 5)
        pool_search_time = time.time() - start_time
        print(f"With pooling: {pool_search_time:.3f}s")
    except Exception as e:
        print(f"With pooling failed: {e}")
        pool_search_time = 0
    
    if no_pool_search_time > 0 and pool_search_time > 0:
        search_improvement = ((no_pool_search_time - pool_search_time) / no_pool_search_time) * 100
        print(f"Search improvement: {search_improvement:.1f}%")
    
    print("\n" + "=" * 60)
    print("EXPECTED BENEFITS")
    print("=" * 60)
    print("- Connection pooling eliminates ~100-200ms overhead per operation")
    print("- Greater benefits with more operations")
    print("- Reduced load on Weaviate cluster")
    print("- Better performance under high concurrency")


def test_pool_behavior():
    """Test connection pool behavior under various conditions."""
    
    print("\n" + "=" * 60)
    print("CONNECTION POOL BEHAVIOR TEST")
    print("=" * 60)
    
    # Reinitialize pool with small size to test overflow
    print("\nInitializing small pool (size=2, overflow=1)...")
    init_weaviate_pool(pool_size=2, max_overflow=1)
    
    # Test concurrent operations
    print("\nTesting concurrent operations...")
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    def perform_operation(op_id):
        try:
            result = get_last_messages_weaviate_pooled(user_table, f"test_{op_id}", 5)
            return f"Op {op_id}: Success ({len(result)} messages)"
        except Exception as e:
            return f"Op {op_id}: Failed - {str(e)}"
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(perform_operation, i) for i in range(5)]
        for future in as_completed(futures):
            print(f"  {future.result()}")
    
    # Check final pool stats
    final_stats = get_pool_statistics()
    print(f"\nFinal Pool Statistics: {json.dumps(final_stats, indent=2)}")
    
    if final_stats.get('pool_exhausted_count', 0) > 0:
        print("\nNote: Pool exhaustion detected - consider increasing pool size")


if __name__ == "__main__":
    print("Testing Weaviate Connection Pooling")
    print("Note: This test requires a valid Weaviate connection")
    print("If Weaviate is not available, the test will show errors\n")
    
    try:
        # Run performance comparison
        test_connection_pooling_performance()
        
        # Run behavior tests
        test_pool_behavior()
        
    except Exception as e:
        print(f"\nTest failed: {e}")
        print("This is expected if Weaviate is not configured or accessible")
"""
Test script to verify parallel processing implementation and measure performance improvements.
This script simulates the lambda function's message retrieval operations.
"""

import time
import json
from typing import Dict, List, Any
from parallel_utils import time_operation, ParallelExecutor
from parallel_storage import get_message_history_parallel, get_relevant_messages_parallel, parallel_preprocessing
from storage import get_last_messages_weaviate, get_relevant_messages, manage_mute_status
from config import user_table, assistant_table


class PerformanceTest:
    """Test harness for comparing serial vs parallel performance."""
    
    def __init__(self, chat_id: str = "test_chat_123"):
        self.chat_id = chat_id
        self.results = {
            "serial": {},
            "parallel": {}
        }
    
    @time_operation("serial_message_retrieval")
    def test_serial_message_retrieval(self, num_messages: int = 10, full_text_len: int = 5):
        """Test the original serial message retrieval."""
        start_time = time.time()
        
        # Serial retrieval
        user_messages_full = get_last_messages_weaviate(user_table, self.chat_id, num_messages)
        assistant_messages_full = get_last_messages_weaviate(assistant_table, self.chat_id, num_messages)
        
        # Process messages
        user_msg_history = user_messages_full[full_text_len:]
        user_messages = user_messages_full[:full_text_len]
        
        asst_msg_history = assistant_messages_full[full_text_len:]
        assistant_messages = assistant_messages_full[:full_text_len]
        
        # Combine and sort
        msg_history = user_msg_history + asst_msg_history
        msg_history.sort(key=lambda x: x['sort_key'])
        
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x['sort_key'])
        
        duration = time.time() - start_time
        self.results["serial"]["message_retrieval"] = duration
        
        return msg_history, all_messages, user_messages, assistant_messages
    
    @time_operation("parallel_message_retrieval")
    def test_parallel_message_retrieval(self, num_messages: int = 10, full_text_len: int = 5):
        """Test the parallel message retrieval."""
        start_time = time.time()
        
        result = get_message_history_parallel(self.chat_id, num_messages, full_text_len)
        
        duration = time.time() - start_time
        self.results["parallel"]["message_retrieval"] = duration
        
        return result
    
    @time_operation("serial_relevance_search")
    def test_serial_relevance_search(self, text: str, relevant_count: int = 5):
        """Test the original serial relevance search."""
        start_time = time.time()
        
        # Serial search
        relevant_user_messages = get_relevant_messages(user_table, self.chat_id, text, relevant_count)
        relevant_assistant_messages = get_relevant_messages(assistant_table, self.chat_id, text, relevant_count)
        
        # Combine and sort
        all_relevant_messages = relevant_user_messages + relevant_assistant_messages
        all_relevant_messages.sort(key=lambda x: x['sort_key'])
        
        duration = time.time() - start_time
        self.results["serial"]["relevance_search"] = duration
        
        return all_relevant_messages
    
    @time_operation("parallel_relevance_search")
    def test_parallel_relevance_search(self, text: str, relevant_count: int = 5):
        """Test the parallel relevance search."""
        start_time = time.time()
        
        result = get_relevant_messages_parallel(self.chat_id, text, relevant_count)
        
        duration = time.time() - start_time
        self.results["parallel"]["relevance_search"] = duration
        
        return result
    
    def run_comparison_tests(self):
        """Run all comparison tests and display results."""
        print("=" * 60)
        print("PERFORMANCE COMPARISON TEST")
        print("=" * 60)
        
        # Test parameters
        num_messages = 10
        full_text_len = 5
        test_text = "test query for relevance search"
        relevant_count = 5
        
        # Test message retrieval
        print("\n1. Testing Message Retrieval...")
        print("-" * 40)
        
        try:
            serial_result = self.test_serial_message_retrieval(num_messages, full_text_len)
            print(f"Serial execution completed: {self.results['serial']['message_retrieval']:.3f}s")
        except Exception as e:
            print(f"Serial execution failed: {e}")
            serial_result = None
        
        try:
            parallel_result = self.test_parallel_message_retrieval(num_messages, full_text_len)
            print(f"Parallel execution completed: {self.results['parallel']['message_retrieval']:.3f}s")
        except Exception as e:
            print(f"Parallel execution failed: {e}")
            parallel_result = None
        
        if serial_result and parallel_result:
            speedup = self.results['serial']['message_retrieval'] / self.results['parallel']['message_retrieval']
            print(f"Speedup: {speedup:.2f}x")
        
        # Test relevance search
        print("\n2. Testing Relevance Search...")
        print("-" * 40)
        
        try:
            serial_relevant = self.test_serial_relevance_search(test_text, relevant_count)
            print(f"Serial execution completed: {self.results['serial']['relevance_search']:.3f}s")
        except Exception as e:
            print(f"Serial execution failed: {e}")
            serial_relevant = None
        
        try:
            parallel_relevant = self.test_parallel_relevance_search(test_text, relevant_count)
            print(f"Parallel execution completed: {self.results['parallel']['relevance_search']:.3f}s")
        except Exception as e:
            print(f"Parallel execution failed: {e}")
            parallel_relevant = None
        
        if serial_relevant and parallel_relevant:
            speedup = self.results['serial']['relevance_search'] / self.results['parallel']['relevance_search']
            print(f"Speedup: {speedup:.2f}x")
        
        # Overall summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        
        total_serial = sum(self.results['serial'].values())
        total_parallel = sum(self.results['parallel'].values())
        
        print(f"Total serial time: {total_serial:.3f}s")
        print(f"Total parallel time: {total_parallel:.3f}s")
        
        if total_serial > 0 and total_parallel > 0:
            overall_speedup = total_serial / total_parallel
            improvement = ((total_serial - total_parallel) / total_serial) * 100
            print(f"Overall speedup: {overall_speedup:.2f}x")
            print(f"Performance improvement: {improvement:.1f}%")
        
        print("\nDetailed Results:")
        print(json.dumps(self.results, indent=2))


def test_parallel_executor():
    """Test the ParallelExecutor class directly."""
    print("\n" + "=" * 60)
    print("TESTING PARALLEL EXECUTOR")
    print("=" * 60)
    
    executor = ParallelExecutor(max_workers=3)
    
    # Define test functions
    def slow_function(n):
        time.sleep(0.5)
        return n * 2
    
    def another_slow_function(s):
        time.sleep(0.3)
        return s.upper()
    
    def fast_function(x, y):
        return x + y
    
    # Create tasks
    tasks = [
        (slow_function, (5,), {}),
        (another_slow_function, ("hello",), {}),
        (fast_function, (10, 20), {})
    ]
    
    # Execute tasks
    start_time = time.time()
    results = executor.execute_parallel_tasks(tasks)
    duration = time.time() - start_time
    
    print(f"Parallel execution time: {duration:.3f}s")
    print(f"Results: {results}")
    
    # Compare with serial execution
    start_time = time.time()
    serial_results = {}
    for idx, (func, args, kwargs) in enumerate(tasks):
        serial_results[idx] = func(*args, **kwargs)
    serial_duration = time.time() - start_time
    
    print(f"Serial execution time: {serial_duration:.3f}s")
    print(f"Speedup: {serial_duration/duration:.2f}x")


if __name__ == "__main__":
    # Test the ParallelExecutor
    test_parallel_executor()
    
    # Run performance comparison tests
    # Note: This requires a valid Weaviate connection and test data
    print("\n" + "=" * 60)
    print("Note: The following tests require a valid Weaviate connection")
    print("and test data in the database. They may fail if not available.")
    print("=" * 60)
    
    try:
        tester = PerformanceTest(chat_id="test_chat_123")
        tester.run_comparison_tests()
    except Exception as e:
        print(f"\nPerformance tests could not be completed: {e}")
        print("This is expected if Weaviate is not configured or test data is not available.")
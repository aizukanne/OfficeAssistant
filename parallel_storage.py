"""
Parallel implementations of storage functions for improved performance.
This module provides parallelized versions of message retrieval and search functions.
Now enhanced with connection pooling support for better resource utilization.
"""

from typing import List, Dict, Any, Tuple, Optional
from parallel_utils import ParallelExecutor, time_operation, time_operation_with_metrics
from storage import transform_objects
from storage_pooled import (
    get_last_messages_weaviate_pooled,
    get_relevant_messages_pooled,
    init_weaviate_pool
)
from config import user_table, assistant_table

# Initialize the connection pool
init_weaviate_pool(pool_size=5, max_overflow=2)

# Use pooled versions for better performance
get_last_messages_weaviate = get_last_messages_weaviate_pooled
get_relevant_messages = get_relevant_messages_pooled


@time_operation("parallel_message_history")
def get_message_history_parallel(chat_id: str, num_messages: int, full_text_len: int) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Retrieve user and assistant message history in parallel.
    
    Args:
        chat_id: The chat identifier
        num_messages: Total number of messages to retrieve
        full_text_len: Number of recent messages to keep separate
        
    Returns:
        Tuple of (msg_history, all_messages, user_messages, assistant_messages)
    """
    executor = ParallelExecutor(max_workers=2)
    
    # Define parallel tasks for user and assistant messages
    tasks = [
        (get_last_messages_weaviate, (user_table, chat_id, num_messages), {}),
        (get_last_messages_weaviate, (assistant_table, chat_id, num_messages), {})
    ]
    
    # Execute tasks in parallel
    results = executor.execute_parallel_tasks(tasks)
    
    # Process results
    user_messages_full = results.get(0, [])
    assistant_messages_full = results.get(1, [])
    
    # Split into history and recent messages
    user_msg_history = user_messages_full[full_text_len:]
    user_messages = user_messages_full[:full_text_len]
    
    asst_msg_history = assistant_messages_full[full_text_len:]
    assistant_messages = assistant_messages_full[:full_text_len]
    
    # Combine and sort history
    msg_history = user_msg_history + asst_msg_history
    msg_history.sort(key=lambda x: x['sort_key'])
    
    # Combine and sort recent messages
    all_messages = user_messages + assistant_messages
    all_messages.sort(key=lambda x: x['sort_key'])
    
    return msg_history, all_messages, user_messages, assistant_messages


@time_operation("parallel_relevance_search")
def get_relevant_messages_parallel(chat_id: str, text: str, relevant_count: int) -> List[Dict]:
    """
    Search for relevant messages in parallel across user and assistant collections.
    
    Args:
        chat_id: The chat identifier
        text: Query text for relevance search
        relevant_count: Number of relevant messages to retrieve
        
    Returns:
        List of relevant messages sorted by timestamp
    """
    if relevant_count <= 0 or not text:
        return []
    
    executor = ParallelExecutor(max_workers=2)
    
    # Define parallel tasks for searching user and assistant messages
    tasks = [
        (get_relevant_messages, (user_table, chat_id, text, relevant_count), {}),
        (get_relevant_messages, (assistant_table, chat_id, text, relevant_count), {})
    ]
    
    # Execute tasks in parallel
    results = executor.execute_parallel_tasks(tasks)
    
    # Combine and sort results
    relevant_user_messages = results.get(0, [])
    relevant_assistant_messages = results.get(1, [])
    
    all_relevant_messages = relevant_user_messages + relevant_assistant_messages
    all_relevant_messages.sort(key=lambda x: x['sort_key'])
    
    return all_relevant_messages


@time_operation_with_metrics("parallel_preprocessing")
def parallel_preprocessing(chat_id: str, text: str, route_name: str, relevant_count: int, 
                         enable_odoo: bool = True) -> Dict[str, Any]:
    """
    Execute all pre-processing tasks in parallel.
    
    Args:
        chat_id: The chat identifier
        text: User input text
        route_name: The determined route name
        relevant_count: Number of relevant messages to search for
        enable_odoo: Whether to fetch Odoo models
        
    Returns:
        Dictionary containing results of all preprocessing tasks
    """
    from odoo_functions import odoo_get_mapped_models
    from storage import manage_mute_status
    
    executor = ParallelExecutor(max_workers=4)
    
    tasks = []
    task_names = []
    
    # Always check mute status
    tasks.append((manage_mute_status, (chat_id,), {}))
    task_names.append('mute_status')
    
    # Conditionally add Odoo models
    if enable_odoo and route_name == 'odoo_erp':
        tasks.append((odoo_get_mapped_models, (), {}))
        task_names.append('odoo_models')
    
    # Add relevance search if needed
    if relevant_count > 0 and text:
        tasks.append((get_relevant_messages_parallel, (chat_id, text, relevant_count), {}))
        task_names.append('relevant_messages')
    
    # Execute all tasks
    results = executor.execute_parallel_tasks(tasks)
    
    # Map results to named dictionary
    named_results = {}
    for idx, name in enumerate(task_names):
        named_results[name] = results.get(idx)
    
    return named_results


@time_operation("batch_message_retrieval")
def batch_retrieve_messages(chat_ids: List[str], num_messages: int = 10) -> Dict[str, List[Dict]]:
    """
    Retrieve messages for multiple chat IDs in parallel.
    
    Args:
        chat_ids: List of chat identifiers
        num_messages: Number of messages to retrieve per chat
        
    Returns:
        Dictionary mapping chat_id to list of messages
    """
    from parallel_utils import batch_process_parallel
    
    def retrieve_for_chat(chat_id):
        user_msgs = get_last_messages_weaviate(user_table, chat_id, num_messages)
        asst_msgs = get_last_messages_weaviate(assistant_table, chat_id, num_messages)
        all_msgs = user_msgs + asst_msgs
        all_msgs.sort(key=lambda x: x['sort_key'])
        return all_msgs
    
    # Process all chat IDs in parallel batches
    results = batch_process_parallel(
        chat_ids, 
        retrieve_for_chat,
        batch_size=10,
        max_workers=5
    )
    
    # Create result dictionary
    chat_messages = {}
    for idx, chat_id in enumerate(chat_ids):
        chat_messages[chat_id] = results[idx] if results[idx] else []
    
    return chat_messages


# Helper function to combine parallel search results
def combine_search_results(user_results: List[Dict], assistant_results: List[Dict], 
                         max_results: Optional[int] = None) -> List[Dict]:
    """
    Combine and deduplicate search results from user and assistant collections.
    
    Args:
        user_results: Search results from user messages
        assistant_results: Search results from assistant messages
        max_results: Maximum number of results to return
        
    Returns:
        Combined and sorted list of unique messages
    """
    # Combine results
    all_results = user_results + assistant_results
    
    # Remove duplicates based on sort_key and chat_id
    seen = set()
    unique_results = []
    
    for msg in all_results:
        key = (msg.get('chat_id'), msg.get('sort_key'))
        if key not in seen:
            seen.add(key)
            unique_results.append(msg)
    
    # Sort by relevance score if available, otherwise by timestamp
    unique_results.sort(key=lambda x: (x.get('relevance_score', 0), x['sort_key']), reverse=True)
    
    # Limit results if specified
    if max_results:
        unique_results = unique_results[:max_results]
    
    return unique_results


# Performance monitoring wrapper for existing functions
def create_monitored_function(original_func, operation_name):
    """
    Create a monitored version of an existing function.
    
    Args:
        original_func: The original function to monitor
        operation_name: Name for the monitoring metrics
        
    Returns:
        Monitored version of the function
    """
    @time_operation_with_metrics(operation_name)
    def monitored_func(*args, **kwargs):
        return original_func(*args, **kwargs)
    
    return monitored_func
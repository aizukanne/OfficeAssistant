"""
Enhanced storage module with connection pooling support.
This module provides pooled versions of storage functions for better performance.
"""

import datetime
import json
import time
from decimal import Decimal
from typing import List, Dict, Any, Optional

from boto3.dynamodb.conditions import Key
from bson import ObjectId
import calendar
from config import dynamodb, weaviate_url, weaviate_api_key, headers, names_table, channels_table, meetings_table, assistant_table, user_table
from weaviate.classes.query import Filter, Sort
from connection_pool import get_weaviate_pool
from parallel_utils import time_operation_with_metrics


# Get the singleton connection pool
weaviate_pool = None

def init_weaviate_pool(pool_size: int = 5, max_overflow: int = 2):
    """Initialize the Weaviate connection pool."""
    global weaviate_pool
    if weaviate_pool is None:
        weaviate_pool = get_weaviate_pool(
            cluster_url=weaviate_url,
            api_key=weaviate_api_key,
            headers=headers,
            pool_size=pool_size,
            max_overflow=max_overflow
        )
    return weaviate_pool


# Import original functions from storage
from storage import (
    decimal_default, transform_objects, save_message, 
    get_last_messages, get_message_by_sort_id, get_messages_in_range,
    get_users, get_channels, manage_mute_status
)


@time_operation_with_metrics("pooled_save_message_weaviate")
def save_message_weaviate_pooled(collection_name, chat_id, text, thread=None, image_urls=None):
    """
    Save a message to Weaviate using connection pool.
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    timestamp = datetime.datetime.now(datetime.timezone.utc)
    
    # Create the message object
    message_object = {
        "chat_id": chat_id,
        "message": text,
        "timestamp": timestamp.isoformat()
    }
    
    # Add thread if provided
    if thread is not None:
        message_object["thread"] = thread
    
    # Add image URLs if provided
    if image_urls is not None:
        message_object["image_urls"] = image_urls
    
    # Use connection from pool
    with pool.get_client() as client:
        try:
            collection = client.collections.get(collection_name)
            collection.data.insert(message_object)
            print(f"Message saved to {collection_name}")
        except Exception as e:
            print(f"Error saving message to Weaviate: {e}")
            raise


@time_operation_with_metrics("pooled_get_last_messages_weaviate")
def get_last_messages_weaviate_pooled(collection_name, chat_id, num_messages):
    """
    Retrieve last messages from Weaviate using connection pool.
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    try:
        with pool.get_client() as client:
            # Retrieve the collection
            collection = client.collections.get(collection_name)
            
            # Create a filter to match the chat_id
            filters = Filter.by_property("chat_id").equal(chat_id)
            
            # Fetch objects with the filter, sorted by timestamp in descending order
            response = collection.query.fetch_objects(
                filters=filters,
                sort=Sort.by_property("timestamp", ascending=False),
                limit=num_messages
            )
            
            if response.objects:
                response_messages = transform_objects(response.objects, collection_name)
            else:
                response_messages = []
            
            return response_messages
    except Exception as e:
        print(f"Error retrieving last messages: {e}")
        return []


@time_operation_with_metrics("pooled_get_relevant_messages")
def get_relevant_messages_pooled(collection_name, chat_id, query_text, num_results):
    """
    Search for relevant messages using connection pool.
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    try:
        with pool.get_client() as client:
            # Retrieve the collection
            collection = client.collections.get(collection_name)

            # Create a filter to match the chat_id
            filters = Filter.by_property("chat_id").equal(chat_id)

            # Perform a hybrid search with the specified query, filter, and alpha=0.9
            response = collection.query.hybrid(
                query=query_text,
                filters=filters,
                limit=num_results,
                alpha=0.9
            )

            print(f'Relevant Results: {response.objects if response.objects else []}')
            
            if response.objects:
                response_messages = transform_objects(response.objects, collection_name)
            else:
                response_messages = []
            
            return response_messages        
    except Exception as e:
        print(f"Error retrieving relevant messages: {e}")
        return []


@time_operation_with_metrics("pooled_get_message_by_sort_id")
def get_message_by_sort_id_pooled(role, chat_id, sort_id):
    """
    Get a specific message by sort_id using connection pool.
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    try:
        with pool.get_client() as client:
            # Determine the appropriate collection based on the role
            if role == "user":
                collection = client.collections.get('UserMessages')
            elif role == "assistant":
                collection = client.collections.get('AssistantMessages')
            else:
                return None  # Handle unexpected roles

            timestamp = int(sort_id)
            timestamp_iso = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()
            
            # Create filters to match chat_id and sort_id
            filters = (
                Filter.by_property("chat_id").equal(chat_id)
                & Filter.by_property("timestamp").equal(timestamp_iso)
            )

            # Fetch the single matching object
            response = collection.query.fetch_objects(
                filters=filters,
                limit=1  # Expecting only one item
            )

            if response.objects:
                # Transform and return the first (and should be only) object
                transformed = transform_objects(response.objects, collection.name)
                return transformed[0] if transformed else None
            else:
                return None
    except Exception as e:
        print(f"Error retrieving message by sort_id: {e}")
        return None


@time_operation_with_metrics("pooled_get_messages_in_range")
def get_messages_in_range_pooled(role, chat_id, start_sort_id, end_sort_id):
    """
    Get messages within a sort_id range using connection pool.
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    try:
        with pool.get_client() as client:
            # Determine the appropriate collection based on the role
            if role == "user":
                collection = client.collections.get('UserMessages')
            elif role == "assistant":
                collection = client.collections.get('AssistantMessages')
            else:
                return []  # Handle unexpected roles

            # Convert sort_ids to timestamps
            start_timestamp = int(start_sort_id)
            end_timestamp = int(end_sort_id)
            
            start_timestamp_iso = datetime.datetime.fromtimestamp(start_timestamp, datetime.timezone.utc).isoformat()
            end_timestamp_iso = datetime.datetime.fromtimestamp(end_timestamp, datetime.timezone.utc).isoformat()

            # Create filters for chat_id and timestamp range
            filters = (
                Filter.by_property("chat_id").equal(chat_id)
                & Filter.by_property("timestamp").greater_or_equal(start_timestamp_iso)
                & Filter.by_property("timestamp").less_or_equal(end_timestamp_iso)
            )

            # Fetch objects within the range, sorted by timestamp
            response = collection.query.fetch_objects(
                filters=filters,
                sort=Sort.by_property("timestamp", ascending=True)
            )

            if response.objects:
                return transform_objects(response.objects, collection.name)
            else:
                return []
    except Exception as e:
        print(f"Error retrieving messages in range: {e}")
        return []


# Batch operations using connection pool
@time_operation_with_metrics("pooled_batch_save_messages")
def batch_save_messages_weaviate_pooled(messages: List[Dict[str, Any]], collection_name: str):
    """
    Save multiple messages in batch using connection pool.
    
    Args:
        messages: List of message dictionaries
        collection_name: Name of the Weaviate collection
    """
    # Ensure pool is initialized
    pool = init_weaviate_pool()
    
    if not messages:
        return
    
    with pool.get_client() as client:
        try:
            collection = client.collections.get(collection_name)
            
            # Prepare batch objects
            batch_objects = []
            for msg in messages:
                timestamp = datetime.datetime.now(datetime.timezone.utc)
                
                message_object = {
                    "chat_id": msg.get("chat_id"),
                    "message": msg.get("message"),
                    "timestamp": timestamp.isoformat()
                }
                
                if msg.get("thread"):
                    message_object["thread"] = msg["thread"]
                
                if msg.get("image_urls"):
                    message_object["image_urls"] = msg["image_urls"]
                
                batch_objects.append(message_object)
            
            # Insert batch
            collection.data.insert_many(batch_objects)
            print(f"Batch saved {len(batch_objects)} messages to {collection_name}")
            
        except Exception as e:
            print(f"Error batch saving messages to Weaviate: {e}")
            raise


# Create pooled versions of functions for drop-in replacement
def create_pooled_storage_functions():
    """
    Create a dictionary of pooled storage functions that can replace the original ones.
    """
    return {
        'save_message_weaviate': save_message_weaviate_pooled,
        'get_last_messages_weaviate': get_last_messages_weaviate_pooled,
        'get_relevant_messages': get_relevant_messages_pooled,
        'get_message_by_sort_id': get_message_by_sort_id_pooled,
        'get_messages_in_range': get_messages_in_range_pooled,
        'batch_save_messages_weaviate': batch_save_messages_weaviate_pooled
    }


# Pool statistics function
def get_pool_statistics():
    """Get statistics from the connection pool."""
    if weaviate_pool:
        return weaviate_pool.get_stats()
    return {"error": "Pool not initialized"}
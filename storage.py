import datetime
import json
import time
from decimal import Decimal
from typing import List, Dict, Any, Optional

from boto3.dynamodb.conditions import Key
from bson import ObjectId
import calendar
from config import dynamodb, weaviate_client, names_table, channels_table, meetings_table, assistant_table, user_table
from weaviate.classes.query import Filter, Sort


# Function to convert non-serializable types for JSON serialization
def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, ObjectId):
        return str(obj)  # Convert ObjectId to string
    raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))


def transform_objects(objects, collection_name):
    transformed_list = []

    for obj in objects:
        # Extract the necessary fields from the properties
        timestamp = obj.properties.get('timestamp')
        message = obj.properties.get('message')
        chat_id = obj.properties.get('chat_id')
        
        # Convert the timestamp to a Unix timestamp (sort_key)
        if timestamp:
            sort_key = calendar.timegm(timestamp.utctimetuple())
        else:
            sort_key = float('inf')  # A large number for missing timestamps

        # Determine the role based on the collection name
        if collection_name == 'UserMessages':
            role = 'user'
        elif collection_name == 'AssistantMessages':
            role = 'assistant'
        else:
            role = 'Unknown'

        # Prepare the transformed dictionary
        transformed_item = {
            "sort_key": sort_key,
            "message": message,
            "chat_id": chat_id,
            "role": role
        }
        
        # Add the transformed item to the list
        transformed_list.append(transformed_item)
    
    return transformed_list


def save_message_weaviate(collection_name, chat_id, text, thread=None, image_urls=None):
    timestamp = int(time.time())
    timestamp_iso = datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).isoformat()

    collection = weaviate_client.collections.get(collection_name)

    properties = {
        "chat_id": chat_id,
        "timestamp": timestamp_iso,
        "message": text
    }
    
    if thread is not None:
        properties["thread"] = thread
    
    if image_urls is not None:
        properties["image_urls"] = image_urls
    
    try:
        collection.data.insert(properties=properties)
        #print("Message saved successfully.")
    except Exception as e:
        print(f"Error saving message: {e}")
        


def get_last_messages_weaviate(collection_name, chat_id, num_messages):
    print(f'Collection Name: {collection_name}')
    try:
        # Retrieve the collection
        collection = weaviate_client.collections.get(collection_name)

        # Create a filter to match the chat_id
        filters = Filter.by_property("chat_id").equal(chat_id)

        # Fetch objects with the specified filter and sorting
        response = collection.query.fetch_objects(
            filters=filters,
            sort=Sort.by_property(name="timestamp", ascending=False),
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


def get_relevant_messages(collection_name, chat_id, query_text, num_results):
    try:
        # Retrieve the collection
        collection = weaviate_client.collections.get(collection_name)

        # Create a filter to match the chat_id
        filters = Filter.by_property("chat_id").equal(chat_id)

        # Perform a hybrid search with the specified query, filter, and alpha=0.8
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


def save_message(table, chat_id, text, role, thread=None, image_urls=None):
    timestamp = int(time.time())
    sort_key = timestamp  # use timestamp as sort key
    ttl = timestamp + 20 * 24 * 60 * 60  # 20 days

    item = {
        'chat_id': chat_id,
        'sort_key': sort_key,
        'message': text,
        'role': role,  # Existing line to save the role of the message  
        'ttl': ttl
    }

    # Add thread to the item if it's provided
    if thread is not None:
        item['thread'] = thread
    
    # Add image urls to the item if they are provided
    if image_urls is not None:
        item['image_urls'] = image_urls

    table_obj = dynamodb.Table(table)
    table_obj.put_item(Item=item)


def get_last_messages(table, chat_id, num_messages):
    table_obj = dynamodb.Table(table)
    response = table_obj.query(
        KeyConditionExpression=Key('chat_id').eq(chat_id),
        Limit=num_messages,
        ScanIndexForward=False  # get the latest messages first
    )
    messages = response['Items'] if 'Items' in response else []
    return messages  # return the whole item, not just the message


def get_message_by_sort_id(role, chat_id, sort_id):
    try:
        # Determine the appropriate collection based on the role
        if role == "user":
            collection = weaviate_client.collections.get('UserMessages')
        elif role == "assistant":
            collection = weaviate_client.collections.get('AssistantMessages')
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

        message = response.objects[0].properties.get('message') if response.objects else None
        print(f"Single Message: {message}")
        return message
    except Exception as e:
        print(f"Error retrieving message by sort ID: {e}")
        return None


def get_messages_in_range(chat_id, start_sort_id, end_sort_id):
    try:
        # Retrieve user and assistant messages
        user_collection = weaviate_client.collections.get("UserMessages")
        assistant_collection = weaviate_client.collections.get("AssistantMessages")

        # Define filters for both collections using the correct timestamp conversion
        start_date = datetime.datetime.fromtimestamp(start_sort_id, datetime.timezone.utc).isoformat()
        end_date = datetime.datetime.fromtimestamp(end_sort_id, datetime.timezone.utc).isoformat()
        print(f"Start Date: {start_date}")
        print(f"End Date: {end_date}")

        # Define filters for both collections
        filters = Filter.by_property("chat_id").equal(chat_id) & Filter.by_property("timestamp").greater_or_equal(start_date) & Filter.by_property("timestamp").less_or_equal(end_date)

        # Fetch user messages
        user_messages_response = user_collection.query.fetch_objects(
            filters=filters
        )
        user_messages = transform_objects(user_messages_response.objects if user_messages_response.objects else [], "UserMessages")
        print(f"User Messages: {user_messages}")

        # Fetch assistant messages
        assistant_messages_response = assistant_collection.query.fetch_objects(
            filters=filters
        )
        assistant_messages = transform_objects(assistant_messages_response.objects if assistant_messages_response.objects else [], "AssistantMessages")
        print(f"Assistant Messages: {assistant_messages}")

        # Combine and sort messages
        all_messages = user_messages + assistant_messages
        all_messages.sort(key=lambda x: x["sort_key"])

        return all_messages
    except Exception as e:
        print(f"Error retrieving messages in range: {e}")
        return []


def get_users(user_id=None):
    try:
        if user_id:
            # Retrieve a single user
            response = names_table.get_item(Key={'user_id': user_id})
            item = response.get('Item', None)
            if item:
                return item
            else:
                from slack_integration import update_slack_users
                update_slack_users()
                response = names_table.get_item(Key={'user_id': user_id})
                item = response.get('Item', None)
                if item:
                    return item
                else:
                    print(user_id, " still not found after update.")
                    return None
        else:
            # Retrieve all users
            response = names_table.scan()
            items = response.get('Items', [])
            return items
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_channels(id=None):
    try:
        from slack_integration import update_slack_conversations
        update_slack_conversations()
        # Perform a scan operation on the table to retrieve all channels  
        response = channels_table.scan()
        channels = response.get('Items', [])

        # Check if there are more channels to fetch
        while 'LastEvaluatedKey' in response:
            response = channels_table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            channels.extend(response.get('Items', []))

        return channels
    except Exception as e:
        print(f"Error fetching channels: {e}")
        return []


def manage_mute_status(chat_id, status=None):
    table = channels_table
    
    if status is not None:
        # Initialize status_bool based on the type and value of status
        if isinstance(status, bool):
            status_bool = status
        elif isinstance(status, str):
            status = status.strip()  # Remove any leading/trailing whitespace
            if status.lower() in ['true', 'false']:
                status_bool = status.lower() == 'true'
            else:
                raise ValueError("String status must be 'true' or 'false' (case insensitive).")
        else:
            raise TypeError("Status must be provided as either a boolean or a string.")

        try:
            response = table.update_item(
                Key={
                    'id': chat_id
                },
                UpdateExpression='SET maria_status = :val',
                ExpressionAttributeValues={
                    ':val': status_bool
                },
                ReturnValues='UPDATED_NEW'
            )
            current_status = "true" if status_bool else "false"
            return [status_bool, f"Current mute status: {current_status}"]
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise
    else:
        try:
            response = table.get_item(
                Key={
                    'id': chat_id
                }
            )
            item = response.get('Item', {})
            maria_status = item.get('maria_status', None)

            if maria_status is None:
                status_bool = False  # Assuming False as default if status doesn't exist
                current_status = "false"
                print("The 'maria_status' attribute does not exist for this record.")
            else:
                status_bool = maria_status  # Assuming maria_status is stored as a boolean
                current_status = "true" if maria_status else "false"
            
            return [status_bool, f"Current mute status: {current_status}"]
        except ClientError as e:
            print(f"An error occurred: {e}")
            raise

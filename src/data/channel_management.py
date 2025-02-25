import requests
from typing import Dict, List, Optional, Any, Union
from botocore.exceptions import ClientError
from ..core.config import (
    SLACK_BOT_TOKEN,
    CHANNELS_TABLE
)
from ..core.error_handlers import DatabaseError, SlackAPIError

def get_channels(channel_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieve channel information from DynamoDB.
    Updates the channel list from Slack before retrieving.

    Args:
        channel_id: Optional channel ID to retrieve specific channel

    Returns:
        List of channel information dictionaries

    Raises:
        DatabaseError: If database operations fail
    """
    try:
        update_slack_conversations()
        
        # Perform a scan operation on the table to retrieve all channels
        response = CHANNELS_TABLE.scan()
        channels = response.get('Items', [])

        # Check if there are more channels to fetch
        while 'LastEvaluatedKey' in response:
            response = CHANNELS_TABLE.scan(
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            channels.extend(response.get('Items', []))

        if channel_id:
            return [channel for channel in channels if channel.get('id') == channel_id]
        return channels

    except ClientError as e:
        raise DatabaseError(
            message="Failed to retrieve channels",
            status_code=500,
            details={"error": str(e)}
        )

def update_slack_conversations() -> None:
    """
    Update the local channel database with current Slack workspace channels.

    Raises:
        SlackAPIError: If Slack API operations fail
        DatabaseError: If database operations fail
    """
    url = 'https://slack.com/api/conversations.list'
    headers = {
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'types': 'public_channel,private_channel'
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        if response.status_code != 200:
            raise SlackAPIError(
                message="Failed to retrieve conversations list from Slack",
                status_code=response.status_code,
                details={"error": response.text}
            )

        conversations_list = response.json().get('channels', [])
        
        for channel in conversations_list:
            channel_id = channel.get('id')
            try:
                # Retrieve the existing channel details from DynamoDB
                existing_channel = CHANNELS_TABLE.get_item(Key={'id': channel_id})
                
                if 'Item' in existing_channel:
                    print(f"Channel {channel_id} already exists in the database.")
                    # Existing channel: update if necessary
                    CHANNELS_TABLE.update_item(
                        Key={'id': channel_id},
                        UpdateExpression="set #info.#name=:n, #info.#is_private=:p, #info.#num_members=:m",
                        ExpressionAttributeValues={
                            ':n': channel.get('name'),
                            ':p': channel.get('is_private'),
                            ':m': channel.get('num_members')
                        },
                        ExpressionAttributeNames={
                            "#info": "info",
                            "#name": "name",
                            "#is_private": "is_private",
                            "#num_members": "num_members"
                        }
                    )
                else:
                    # New channel: add to the database
                    CHANNELS_TABLE.put_item(Item=channel)
                    print(f"Channel {channel_id} added to the database.")

            except ClientError as e:
                raise DatabaseError(
                    message=f"Error updating channel {channel_id}",
                    status_code=500,
                    details={"error": str(e)}
                )

    except requests.exceptions.RequestException as e:
        raise SlackAPIError(
            message="Failed to communicate with Slack API",
            status_code=500,
            details={"error": str(e)}
        )

def manage_mute_status(chat_id: str, status: Optional[Union[bool, str]] = None) -> List[Union[bool, str]]:
    """
    Manage the mute status of a channel.

    Args:
        chat_id: The ID of the channel
        status: Optional new status to set (True/False or 'true'/'false')

    Returns:
        List containing [current_status, status_message]

    Raises:
        DatabaseError: If database operations fail
        ValueError: If invalid status provided
    """
    try:
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

            # Update the status
            response = CHANNELS_TABLE.update_item(
                Key={'id': chat_id},
                UpdateExpression='SET maria_status = :val',
                ExpressionAttributeValues={':val': status_bool},
                ReturnValues='UPDATED_NEW'
            )
            current_status = "true" if status_bool else "false"
            return [status_bool, f"Current mute status: {current_status}"]
        else:
            # Get current status
            response = CHANNELS_TABLE.get_item(Key={'id': chat_id})
            item = response.get('Item', {})
            maria_status = item.get('maria_status', False)  # Default to False if not set

            current_status = "true" if maria_status else "false"
            return [maria_status, f"Current mute status: {current_status}"]

    except ClientError as e:
        raise DatabaseError(
            message="Failed to manage mute status",
            status_code=500,
            details={"error": str(e)}
        )
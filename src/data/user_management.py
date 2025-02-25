import requests
from typing import Dict, List, Optional, Any
from botocore.exceptions import ClientError
from ..core.config import (
    SLACK_BOT_TOKEN,
    NAMES_TABLE
)
from ..core.error_handlers import DatabaseError, SlackAPIError

def get_users(user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve user information from DynamoDB. If user doesn't exist, 
    fetch from Slack and update DynamoDB.

    Args:
        user_id: Optional user ID to retrieve specific user

    Returns:
        User information dictionary or list of users

    Raises:
        DatabaseError: If database operations fail
        SlackAPIError: If Slack API operations fail
    """
    try:
        if user_id:
            # Retrieve a single user
            response = NAMES_TABLE.get_item(Key={'user_id': user_id})
            item = response.get('Item')
            
            if item:
                return item
            else:
                # User not found, update from Slack
                update_slack_users()
                response = NAMES_TABLE.get_item(Key={'user_id': user_id})
                item = response.get('Item')
                
                if item:
                    return item
                else:
                    print(f"{user_id} still not found after update.")
                    return None
        else:
            # Retrieve all users
            response = NAMES_TABLE.scan()
            return response.get('Items', [])
            
    except ClientError as e:
        raise DatabaseError(
            message="Failed to retrieve user(s)",
            status_code=500,
            details={"error": str(e)}
        )

def update_slack_users() -> None:
    """
    Update the local user database with current Slack workspace users.

    Raises:
        SlackAPIError: If Slack API operations fail
        DatabaseError: If database operations fail
    """
    url = 'https://slack.com/api/users.list'
    headers = {
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        if response.status_code != 200:
            raise SlackAPIError(
                message="Failed to retrieve users list from Slack",
                status_code=response.status_code,
                details={"error": response.text}
            )

        users_list = response.json().get('members', [])
        
        for user in users_list:
            if not user.get('deleted', True) and not user.get('is_bot', True) and not user.get('is_app_user', True):
                user_id = user.get('id')
                try:
                    response = NAMES_TABLE.get_item(Key={'user_id': user_id})
                    item = response.get('Item')
                    
                    if item:
                        # Check if all keys are available
                        missing_keys = [key for key in ['real_name', 'display_name', 'email'] 
                                     if key not in item]
                        
                        if missing_keys:
                            print(f"Updating user {user_id} with missing keys: {missing_keys}")
                            for key in missing_keys:
                                item[key] = user.get('profile', {}).get(key, '')
                            NAMES_TABLE.put_item(Item=item)
                            print(f"User {user_id} updated successfully.")
                    else:
                        print(f"Adding user {user_id} to the database.")
                        user_data = {
                            'user_id': user_id,
                            'real_name': user.get('profile', {}).get('real_name', ''),
                            'display_name': user.get('profile', {}).get('display_name', ''),
                            'email': user.get('profile', {}).get('email', '')
                        }
                        NAMES_TABLE.put_item(Item=user_data)
                        print(f"User {user_id} added successfully.")
                        
                except ClientError as e:
                    raise DatabaseError(
                        message=f"Error processing user {user_id}",
                        status_code=500,
                        details={"error": str(e)}
                    )

    except requests.exceptions.RequestException as e:
        raise SlackAPIError(
            message="Failed to communicate with Slack API",
            status_code=500,
            details={"error": str(e)}
        )

def get_slack_user_name(user_id: str) -> Dict[str, str]:
    """
    Get the name of a Slack user by their ID.

    Args:
        user_id: The user ID to look up

    Returns:
        Dictionary containing user information

    Raises:
        SlackAPIError: If Slack API operations fail
    """
    url = 'https://slack.com/api/users.info'
    headers = {
        'Authorization': f'Bearer {SLACK_BOT_TOKEN}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    params = {
        'user': user_id
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        if response.status_code == 200:
            user_info = response.json()
            if user_info.get('ok'):
                return {
                    "User Name": user_info['user']['profile']['real_name'],
                    "Display Name": user_info['user']['profile']['display_name'],
                    "Email": user_info['user']['profile']['email']
                }
            else:
                raise SlackAPIError(
                    message="Failed to retrieve user info",
                    status_code=400,
                    details={"error": user_info.get('error', 'Unknown error occurred')}
                )
        else:
            raise SlackAPIError(
                message="Failed to retrieve user info",
                status_code=response.status_code,
                details={"error": f"HTTP Error: {response.status_code}"}
            )
            
    except requests.exceptions.RequestException as e:
        raise SlackAPIError(
            message="Failed to communicate with Slack API",
            status_code=500,
            details={"error": str(e)}
        )

def smart_send_message(message: str, user_name: str) -> str:
    """
    Intelligently send a message to a user by matching their name.

    Args:
        message: The message to send
        user_name: The name of the user to send to

    Returns:
        Status message indicating the result

    Raises:
        SlackAPIError: If Slack API operations fail
    """
    users = get_users()
    matched_users = []
    similar_users = []

    for user in users:
        names = [user.get('real_name', ''), user.get('display_name', '')]
        for name in names:
            if user_name.lower() == name.lower():
                matched_users.append(user)
            elif user_name.lower() in name.lower().split():
                similar_users.append(user)

    if len(matched_users) == 1:
        user_id = matched_users[0]['user_id']
        send_slack_message(user_id, message, None)  # This will need to be imported from slack_client
        return f"Message sent to {matched_users[0]['real_name']} ({matched_users[0]['display_name']})."
    elif len(matched_users) > 1:
        return "Multiple matches found. Please confirm the user: " + ", ".join(
            [f"{u['real_name']} ({u['display_name']})" for u in matched_users]
        )
    elif similar_users:
        return "No exact match found. Did you mean: " + ", ".join(
            [f"{u['real_name']} ({u['display_name']})" for u in similar_users]
        ) + "?"
    else:
        return "No matching user found."
# User Management

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Message Management](message-management.md)

Maria interacts with Slack users and channels, providing capabilities for user information retrieval and management.

## User Operations

Maria can retrieve and work with user information:

### Get Users

```python
def get_users(user_id=None)
```

This function retrieves user information from storage:

**Parameters:**
- `user_id`: (Optional) The ID of a specific user to retrieve

**Returns:**
- If `user_id` is provided: Information for the specified user
- If `user_id` is not provided: Information for all users

**Example:**
```python
# Get all users
all_users = get_users()

# Get a specific user
user = get_users("U12345")
```

**Example Usage:**

```
User: Who is in this workspace?
Maria: There are 25 members in this workspace. The most active users are:
- John Smith (Marketing)
- Sarah Johnson (Product)
- Michael Chen (Engineering)
- Lisa Rodriguez (Sales)
- David Kim (Design)
```

### Send Messages to Users

Maria can send direct messages to specific users:

```python
def send_slack_message(message, channel, ts=None)
```

When used with a user's direct message channel:

**Parameters:**
- `message`: The message text to send
- `channel`: The user's direct message channel ID
- `ts`: (Optional) Thread timestamp if replying to a thread

**Example:**
```python
send_slack_message("Your meeting starts in 15 minutes", "D12345")
```

**Example Usage:**

```
User: Can you remind the team about tomorrow's meeting?
Maria: I'll send a reminder to each team member about tomorrow's meeting.
[Sends direct messages to team members]
I've sent reminders to all 5 team members.
```

### Manage Mute Status

```python
def manage_mute_status(chat_id, status=None)
```

This function manages whether Maria responds to messages in a specific chat:

**Parameters:**
- `chat_id`: The ID of the chat
- `status`: (Optional) The new mute status (True/False)

**Returns:**
- If `status` is provided: Updates the mute status and returns the new status
- If `status` is not provided: Returns the current mute status

**Example:**
```python
# Mute a chat
manage_mute_status("C12345", True)

# Unmute a chat
manage_mute_status("C12345", False)

# Get current mute status
status = manage_mute_status("C12345")
```

**Example Usage:**

```
User: Please mute notifications in this channel
Maria: I've muted notifications for this channel. I won't respond to messages here unless I'm directly mentioned.

User: @Maria please unmute this channel
Maria: I've unmuted this channel. I'll now respond to all messages in this channel.
```

## Channel Operations

Maria can work with Slack channels:

### Get Channels

```python
def get_channels(id=None)
```

This function retrieves channel information from storage:

**Parameters:**
- `id`: (Optional) The ID of a specific channel to retrieve

**Returns:**
- If `id` is provided: Information for the specified channel
- If `id` is not provided: Information for all channels

**Example:**
```python
# Get all channels
all_channels = get_channels()

# Get a specific channel
channel = get_channels("C12345")
```

**Example Usage:**

```
User: What channels am I part of?
Maria: You are currently a member of the following channels:
- #general
- #marketing
- #product-updates
- #random
- #team-announcements
```

### Send Messages to Channels

Maria can send messages to specific channels:

```python
def send_slack_message(message, channel, ts=None)
```

When used with a channel ID:

**Parameters:**
- `message`: The message text to send
- `channel`: The channel ID
- `ts`: (Optional) Thread timestamp if replying to a thread

**Example:**
```python
send_slack_message("The weekly report is now available", "C12345")
```

**Example Usage:**

```
User: Please announce the new product launch in the #announcements channel
Maria: I'll announce the product launch in the #announcements channel.
[Sends message to #announcements]
I've posted the announcement in the #announcements channel.
```

## Implementation Details

### User Data Storage

User information is stored in DynamoDB with the following structure:

```json
{
  "id": "U12345",
  "name": "john.smith",
  "real_name": "John Smith",
  "display_name": "John",
  "email": "john.smith@example.com",
  "title": "Marketing Manager",
  "team_id": "T67890",
  "is_admin": false,
  "is_owner": false,
  "is_bot": false,
  "updated": "2023-01-15T12:30:45Z"
}
```

### Channel Data Storage

Channel information is stored in DynamoDB with the following structure:

```json
{
  "id": "C12345",
  "name": "marketing",
  "is_channel": true,
  "is_group": false,
  "is_im": false,
  "is_private": false,
  "created": "2022-06-10T09:15:30Z",
  "creator": "U67890",
  "is_archived": false,
  "is_general": false,
  "members_count": 15,
  "topic": "Marketing discussions and updates",
  "purpose": "Coordinate marketing activities and campaigns"
}
```

### User and Channel Synchronization

User and channel data is synchronized with Slack:

```python
def update_slack_users():
    """Update the local database with current Slack users."""
    try:
        # Get users from Slack API
        response = slack_client.users_list()
        
        if not response["ok"]:
            logger.error(f"Error getting users: {response['error']}")
            return False
        
        # Update users in database
        for user in response["members"]:
            # Extract user data
            user_data = {
                "id": user["id"],
                "name": user.get("name", ""),
                "real_name": user.get("real_name", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "title": user.get("profile", {}).get("title", ""),
                "team_id": user.get("team_id", ""),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "is_bot": user.get("is_bot", False),
                "updated": datetime.now().isoformat()
            }
            
            # Save to database
            save_user(user_data)
        
        return True
    except Exception as e:
        logger.error(f"Error updating users: {str(e)}")
        return False

def update_slack_conversations():
    """Update the local database with current Slack channels."""
    # Similar implementation for channels
```

### User Lookup

User information can be retrieved by ID or other attributes:

```python
def get_slack_user_name(user_id):
    """Get a user's name from their ID."""
    user = get_users(user_id)
    
    if user:
        return user.get("real_name") or user.get("display_name") or user.get("name")
    
    return "Unknown User"
```

## Best Practices

When working with user management:

- Respect user privacy and data protection regulations
- Keep user information up to date with regular synchronization
- Integrate with [Privacy & Security](privacy-security.md) features for comprehensive data protection
- Use appropriate permission checks before accessing user data
- Consider user time zones when sending messages
- Implement proper error handling for user operations

## Future Enhancements

Planned enhancements for user management include:

- User preference management
- Role-based access control
- User activity tracking
- Enhanced user analytics
- Multi-workspace user correlation

---

[← Back to Main](../README.md) | [← Functionality Overview](README.md) | [← Message Management](message-management.md)
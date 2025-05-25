"""
Unified messaging system for Office Assistant

This module provides a platform-agnostic messaging interface that supports
multiple messaging platforms (Slack, Telegram, etc.) through a common API.

The architecture consists of:
- MessageSender: Abstract base class defining the messaging interface
- MessageRouter: Central router that dispatches messages to appropriate platforms
- Platform-specific implementations: SlackMessenger, TelegramMessenger, etc.

Usage:
    from messaging.router import MessageRouter
    
    router = MessageRouter()
    router.send_message('slack', chat_id, message, thread_ts)
    router.send_message('telegram', chat_id, message)
"""

from .base import MessageSender
from .router import MessageRouter
from .slack_messenger import SlackMessenger
from .telegram_messenger import TelegramMessenger

__all__ = [
    'MessageSender',
    'MessageRouter', 
    'SlackMessenger',
    'TelegramMessenger'
]

__version__ = '1.0.0'
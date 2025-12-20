"""
Conversation Memory Service: Maintains session-based conversation history.

This module provides a simple in-memory store for conversation history.
In production, this should be replaced with a persistent store (Redis, database, etc.).
"""

from typing import List, Dict, Optional
from datetime import datetime, timedelta
import uuid

# In-memory store: session_id -> list of messages
# Format: {"role": "user"|"assistant", "content": str, "timestamp": datetime}
_conversation_store: Dict[str, List[Dict]] = {}

# Session expiry: 24 hours
SESSION_EXPIRY_HOURS = 24


def get_or_create_session(session_id: Optional[str] = None) -> str:
    """
    Get existing session ID or create a new one.
    
    Args:
        session_id: Optional existing session ID
        
    Returns:
        Session ID (existing or newly created)
    """
    if session_id and session_id in _conversation_store:
        return session_id
    
    # Create new session
    new_session_id = str(uuid.uuid4())
    _conversation_store[new_session_id] = []
    return new_session_id


def add_message(session_id: str, role: str, content: str) -> None:
    """
    Add a message to the conversation history.
    
    Args:
        session_id: Session identifier
        role: "user" or "assistant"
        content: Message content
    """
    if session_id not in _conversation_store:
        _conversation_store[session_id] = []
    
    _conversation_store[session_id].append({
        "role": role,
        "content": content,
        "timestamp": datetime.now()
    })


def get_conversation_history(session_id: str, max_messages: int = 10) -> List[Dict]:
    """
    Get recent conversation history for a session.
    
    Args:
        session_id: Session identifier
        max_messages: Maximum number of recent messages to return (default: 10)
        
    Returns:
        List of message dictionaries, most recent first
    """
    if session_id not in _conversation_store:
        return []
    
    messages = _conversation_store[session_id]
    # Return most recent messages
    return messages[-max_messages:]


def format_conversation_context(messages: List[Dict]) -> str:
    """
    Format conversation history as a context string for the LLM.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Formatted conversation context string
    """
    if not messages:
        return ""
    
    context_parts = []
    for msg in messages:
        role = msg["role"].capitalize()
        content = msg["content"]
        context_parts.append(f"{role}: {content}")
    
    return "\n".join(context_parts)


def cleanup_expired_sessions() -> None:
    """
    Remove expired sessions from memory.
    This should be called periodically in production.
    """
    now = datetime.now()
    expired_sessions = []
    
    for session_id, messages in _conversation_store.items():
        if messages:
            oldest_message = messages[0]["timestamp"]
            if now - oldest_message > timedelta(hours=SESSION_EXPIRY_HOURS):
                expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del _conversation_store[session_id]


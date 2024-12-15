# src/modules/chat/memory/short_term.py
from collections import defaultdict, deque
from typing import Dict, List
import time


class ShortTermMemory:
    """Manages short-term conversation memory using circular buffers"""

    def __init__(self, max_messages: int = 50, ttl: int = 6300):
        self.max_messages = max_messages
        self.ttl = ttl
        self.conversations: Dict[int, deque] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )
        self.timestamps: Dict[int, float] = {}

    def add_message(
        self, channel_id: int, user_id: int, content: str, is_bot: bool
    ) -> None:
        """Add a message to the conversation memory"""
        self.conversations[channel_id].append(
            {
                "user_id": user_id,
                "content": content,
                "timestamp": time.time(),
                "is_bot": is_bot,
            }
        )
        self.timestamps[channel_id] = time.time()

    def get_context(self, channel_id: int) -> List[dict]:
        """Get recent conversation context for a channel"""
        # Clear expired conversations
        self._clear_expired()

        # Return conversation history or empty list if none exists
        return list(self.conversations.get(channel_id, []))

    def _clear_expired(self) -> None:
        """Remove expired conversations"""
        current_time = time.time()
        expired_channels = [
            channel_id
            for channel_id, timestamp in self.timestamps.items()
            if current_time - timestamp > self.ttl
        ]

        for channel_id in expired_channels:
            del self.conversations[channel_id]
            del self.timestamps[channel_id]

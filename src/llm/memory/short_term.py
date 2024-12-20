import json
import time
from typing import Dict, Any, List, Optional
import asyncio

from src.services.cache.main import RedisCache


class ShortTermMemory:
    """
    A short-term memory implementation using Redis as a backend.
    This memory acts as a circular buffer:
      • Stores a maximum of 30 messages
      • Applies a TTL of 1 hour 45 minutes (6300 seconds)
      • Maintains insertion order
    """

    DEFAULT_MAX_MESSAGES = 30
    DEFAULT_TTL_SECONDS = 60 * 60 + 45 * 60  # 1 hour 45 minutes

    def __init__(self, session_id: str, redis_cache: RedisCache):
        self.session_id = session_id
        self.cache = redis_cache
        self.memory_key = f"short_term:{self.session_id}"

    async def add_message(
        self, role: str, content: str, extra: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Add a message to the buffer, removing the oldest if at capacity.
        """
        await self._ensure_initialized()
        history = await self._fetch_history_internal()
        new_entry = {"role": role, "content": content, "timestamp": time.time()}
        if extra:
            new_entry.update(extra)

        if len(history) >= self.DEFAULT_MAX_MESSAGES:
            history.pop(0)  # Drop oldest

        history.append(new_entry)
        await self._store_history_internal(history)

    async def get_history(self) -> List[Dict[str, Any]]:
        """Retrieve the conversation history from memory."""
        await self._ensure_initialized()
        return await self._fetch_history_internal()

    async def clear(self) -> None:
        """Clear the buffer for this session."""
        await self.cache.delete(self.memory_key)

    async def _ensure_initialized(self) -> None:
        """
        Ensure the Redis key is initialized and has the correct TTL set.
        """
        exists = await self.cache.exists(self.memory_key)
        if not exists:
            await self._store_history_internal([])

    async def _fetch_history_internal(self) -> List[Dict[str, Any]]:
        """
        Internal method to fetch from Redis and parse JSON.
        """
        data = await self.cache.get(self.memory_key)
        if not data:
            return []
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return []

    async def _store_history_internal(self, history: List[Dict[str, Any]]) -> None:
        """
        Internal method to store history in Redis as JSON, with TTL applied/renewed.
        """
        data = json.dumps(history)
        await self.cache.set(self.memory_key, data, ttl=self.DEFAULT_TTL_SECONDS)

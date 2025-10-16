import redis.asyncio as redis
import json
from typing import Optional, Dict, Any
from datetime import datetime
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RedisService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        self.session_timeout = settings.SESSION_TIMEOUT_MINUTES * 60  # Convert to seconds

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("Successfully connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

    async def close(self):
        """Close Redis connection"""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")

    def _get_session_key(self, phone_number: str) -> str:
        """Generate session key for phone number"""
        return f"session:{phone_number}"

    async def get_session(self, phone_number: str) -> Optional[Dict[str, Any]]:
        """Get session data for a phone number"""
        try:
            key = self._get_session_key(phone_number)
            data = await self.redis.get(key)
            if data:
                session = json.loads(data)
                # Refresh TTL on access
                await self.redis.expire(key, self.session_timeout)
                return session
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    async def set_session(self, phone_number: str, session_data: Dict[str, Any]):
        """Set session data for a phone number"""
        try:
            key = self._get_session_key(phone_number)
            session_data["last_activity"] = datetime.utcnow().isoformat()
            await self.redis.setex(
                key,
                self.session_timeout,
                json.dumps(session_data, default=str)
            )
        except Exception as e:
            logger.error(f"Error setting session: {e}")
            raise

    async def update_session(self, phone_number: str, updates: Dict[str, Any]):
        """Update specific fields in session"""
        try:
            session = await self.get_session(phone_number)
            if session is None:
                session = {}
            session.update(updates)
            await self.set_session(phone_number, session)
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            raise

    async def delete_session(self, phone_number: str):
        """Delete session for a phone number"""
        try:
            key = self._get_session_key(phone_number)
            await self.redis.delete(key)
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            raise

    async def add_to_conversation(self, phone_number: str, role: str, message: str):
        """Add a message to conversation history in session"""
        try:
            session = await self.get_session(phone_number) or {}
            if "conversation" not in session:
                session["conversation"] = []

            session["conversation"].append({
                "role": role,
                "message": message,
                "timestamp": datetime.utcnow().isoformat()
            })

            # Keep only last 20 messages in session for context
            if len(session["conversation"]) > 20:
                session["conversation"] = session["conversation"][-20:]

            await self.set_session(phone_number, session)
        except Exception as e:
            logger.error(f"Error adding to conversation: {e}")
            raise

    async def get_conversation_history(self, phone_number: str) -> list:
        """Get conversation history from session"""
        try:
            session = await self.get_session(phone_number)
            if session and "conversation" in session:
                return session["conversation"]
            return []
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return []


# Singleton instance
redis_client = RedisService()
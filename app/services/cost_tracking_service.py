"""
Service to track LLM API costs
"""
import redis.asyncio as redis
from datetime import datetime, timedelta
from typing import Dict, Optional
from app.core.config import settings
import logging
import json

logger = logging.getLogger(__name__)


class CostTrackingService:
    def __init__(self):
        self.redis: Optional[redis.Redis] = None
        # Gemini Flash pricing (as of 2024)
        self.INPUT_COST_PER_1M = 0.075  # USD
        self.OUTPUT_COST_PER_1M = 0.30  # USD
        self.USD_TO_PKR = 280  # Approximate exchange rate

    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = await redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("Cost tracking service connected to Redis")
        except Exception as e:
            logger.error(f"Failed to connect cost tracking to Redis: {e}")

    async def track_usage(
            self,
            input_tokens: int,
            output_tokens: int,
            phone_number: str
    ) -> Dict[str, float]:
        """Track token usage and calculate costs"""
        try:
            # Calculate costs
            input_cost_usd = (input_tokens / 1_000_000) * self.INPUT_COST_PER_1M
            output_cost_usd = (output_tokens / 1_000_000) * self.OUTPUT_COST_PER_1M
            total_cost_usd = input_cost_usd + output_cost_usd
            total_cost_pkr = total_cost_usd * self.USD_TO_PKR

            # Store in Redis
            today = datetime.utcnow().strftime("%Y-%m-%d")
            daily_key = f"cost:daily:{today}"
            monthly_key = f"cost:monthly:{datetime.utcnow().strftime('%Y-%m')}"
            user_key = f"cost:user:{phone_number}:{today}"

            if self.redis:
                # Increment daily totals
                await self.redis.hincrby(daily_key, "input_tokens", input_tokens)
                await self.redis.hincrby(daily_key, "output_tokens", output_tokens)
                await self.redis.hincrbyfloat(daily_key, "cost_usd", total_cost_usd)
                await self.redis.hincrbyfloat(daily_key, "cost_pkr", total_cost_pkr)
                await self.redis.hincrby(daily_key, "requests", 1)
                await self.redis.expire(daily_key, 86400 * 90)  # Keep for 90 days

                # Increment monthly totals
                await self.redis.hincrby(monthly_key, "input_tokens", input_tokens)
                await self.redis.hincrby(monthly_key, "output_tokens", output_tokens)
                await self.redis.hincrbyfloat(monthly_key, "cost_usd", total_cost_usd)
                await self.redis.hincrbyfloat(monthly_key, "cost_pkr", total_cost_pkr)
                await self.redis.hincrby(monthly_key, "requests", 1)
                await self.redis.expire(monthly_key, 86400 * 365)  # Keep for 1 year

                # Increment user totals
                await self.redis.hincrby(user_key, "input_tokens", input_tokens)
                await self.redis.hincrby(user_key, "output_tokens", output_tokens)
                await self.redis.hincrbyfloat(user_key, "cost_pkr", total_cost_pkr)
                await self.redis.expire(user_key, 86400 * 30)  # Keep for 30 days

            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": input_tokens + output_tokens,
                "input_cost_usd": input_cost_usd,
                "output_cost_usd": output_cost_usd,
                "total_cost_usd": total_cost_usd,
                "total_cost_pkr": total_cost_pkr
            }

        except Exception as e:
            logger.error(f"Error tracking costs: {e}")
            return {}

    async def get_daily_stats(self, date: Optional[str] = None) -> Dict:
        """Get daily cost statistics"""
        try:
            if not date:
                date = datetime.utcnow().strftime("%Y-%m-%d")

            key = f"cost:daily:{date}"

            if self.redis:
                stats = await self.redis.hgetall(key)
                if stats:
                    return {
                        "date": date,
                        "input_tokens": int(stats.get("input_tokens", 0)),
                        "output_tokens": int(stats.get("output_tokens", 0)),
                        "total_tokens": int(stats.get("input_tokens", 0)) + int(stats.get("output_tokens", 0)),
                        "cost_usd": float(stats.get("cost_usd", 0)),
                        "cost_pkr": float(stats.get("cost_pkr", 0)),
                        "requests": int(stats.get("requests", 0))
                    }

            return {}
        except Exception as e:
            logger.error(f"Error getting daily stats: {e}")
            return {}

    async def get_monthly_stats(self, month: Optional[str] = None) -> Dict:
        """Get monthly cost statistics"""
        try:
            if not month:
                month = datetime.utcnow().strftime("%Y-%m")

            key = f"cost:monthly:{month}"

            if self.redis:
                stats = await self.redis.hgetall(key)
                if stats:
                    return {
                        "month": month,
                        "input_tokens": int(stats.get("input_tokens", 0)),
                        "output_tokens": int(stats.get("output_tokens", 0)),
                        "total_tokens": int(stats.get("input_tokens", 0)) + int(stats.get("output_tokens", 0)),
                        "cost_usd": float(stats.get("cost_usd", 0)),
                        "cost_pkr": float(stats.get("cost_pkr", 0)),
                        "requests": int(stats.get("requests", 0)),
                        "avg_cost_per_request_pkr": float(stats.get("cost_pkr", 0)) / max(int(stats.get("requests", 1)),
                                                                                          1)
                    }

            return {}
        except Exception as e:
            logger.error(f"Error getting monthly stats: {e}")
            return {}


# Singleton instance
cost_tracking_service = CostTrackingService()
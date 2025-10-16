from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database_models import Order, OrderStatus, OrderType, MenuItem
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)


class OrderService:
    @staticmethod
    async def create_order(
            db: AsyncSession,
            customer_id: int,
            order_type: OrderType,
            items: List[Dict[str, Any]],
            total_price: float,
            delivery_address: Optional[str] = None,
            delivery_latitude: Optional[float] = None,
            delivery_longitude: Optional[float] = None
    ) -> Order:
        """Create a new order"""
        try:
            # Calculate estimated completion time
            # Dine-in: 20 mins, Takeaway: 15 mins, Delivery: 45 mins
            minutes_map = {
                OrderType.DINE_IN: 20,
                OrderType.TAKEAWAY: 15,
                OrderType.DELIVERY: 45
            }
            estimated_time = datetime.utcnow() + timedelta(minutes=minutes_map[order_type])

            order = Order(
                customer_id=customer_id,
                order_type=order_type,
                status=OrderStatus.PENDING,
                items=json.dumps(items),
                total_price=total_price,
                delivery_address=delivery_address,
                delivery_latitude=delivery_latitude,
                delivery_longitude=delivery_longitude,
                estimated_completion_time=estimated_time
            )

            db.add(order)
            await db.commit()
            await db.refresh(order)
            logger.info(f"Created order {order.id} for customer {customer_id}")
            return order

        except Exception as e:
            logger.error(f"Error creating order: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_order(db: AsyncSession, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            return None

    @staticmethod
    async def update_order_status(
            db: AsyncSession,
            order_id: int,
            status: OrderStatus
    ) -> Optional[Order]:
        """Update order status"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()

            if not order:
                return None

            order.status = status
            order.updated_at = datetime.utcnow()

            if status == OrderStatus.COMPLETED:
                order.completed_at = datetime.utcnow()

            await db.commit()
            await db.refresh(order)
            return order

        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def should_request_feedback(order: Order) -> bool:
        """Check if enough time has passed to request feedback"""
        if order.feedback_requested or order.feedback:
            return False

        if not order.completed_at:
            return False

        time_since_completion = datetime.utcnow() - order.completed_at
        threshold = timedelta(minutes=settings.FEEDBACK_DELAY_MINUTES)

        return time_since_completion >= threshold

    @staticmethod
    async def mark_feedback_requested(db: AsyncSession, order_id: int):
        """Mark that feedback has been requested for an order"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()

            if order:
                order.feedback_requested = True
                await db.commit()
        except Exception as e:
            logger.error(f"Error marking feedback requested: {e}")
            await db.rollback()

    @staticmethod
    async def save_feedback(db: AsyncSession, order_id: int, feedback: str):
        """Save customer feedback for an order"""
        try:
            result = await db.execute(
                select(Order).where(Order.id == order_id)
            )
            order = result.scalar_one_or_none()

            if order:
                order.feedback = feedback
                await db.commit()
        except Exception as e:
            logger.error(f"Error saving feedback: {e}")
            await db.rollback()

    @staticmethod
    async def get_menu_items(db: AsyncSession) -> List[MenuItem]:
        """Get all menu items"""
        try:
            result = await db.execute(select(MenuItem))
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting menu items: {e}")
            return []

    @staticmethod
    def format_menu_for_ai(menu_items: List[MenuItem]) -> str:
        """Format menu items for AI context"""
        if not menu_items:
            return "Menu not available"

        menu_text = ""

        # Group items by category
        categories = {}
        for item in menu_items:
            if item.category not in categories:
                categories[item.category] = []
            categories[item.category].append(item)

        # Format each category
        for category, items in categories.items():
            menu_text += f"\n**{category.upper()}**\n"
            menu_text += "-" * 40 + "\n"

            for item in items:
                # Main item info
                menu_text += f"• {item.item_name}: Rs. {int(item.price_with_tax)}"

                # Add description if available
                if item.description:
                    menu_text += f"\n  Description: {item.description}"

                # Add options if available
                if item.options:
                    menu_text += f"\n  Options: {item.options}"

                # Add synonyms if available (helps AI recognize variations)
                if item.synonyms:
                    menu_text += f"\n  Also known as: {item.synonyms}"

                menu_text += "\n\n"

        return menu_text


order_service = OrderService()
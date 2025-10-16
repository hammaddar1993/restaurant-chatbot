from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.database_models import Customer, Order, Complaint, Reservation, ConversationHistory
from typing import Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CustomerService:
    @staticmethod
    async def get_or_create_customer(db: AsyncSession, phone_number: str) -> Customer:
        """Get existing customer or create new one"""
        try:
            # Try to find existing customer
            result = await db.execute(
                select(Customer).where(Customer.phone_number == phone_number)
            )
            customer = result.scalar_one_or_none()

            if customer:
                return customer

            # Create new customer
            customer = Customer(phone_number=phone_number)
            db.add(customer)
            await db.commit()
            await db.refresh(customer)
            logger.info(f"Created new customer: {phone_number}")
            return customer

        except Exception as e:
            logger.error(f"Error getting/creating customer: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_customer_info(
            db: AsyncSession,
            customer_id: int,
            name: Optional[str] = None,
            address: Optional[str] = None,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None
    ) -> Customer:
        """Update customer information"""
        try:
            result = await db.execute(
                select(Customer).where(Customer.id == customer_id)
            )
            customer = result.scalar_one()

            if name:
                customer.name = name
            if address:
                customer.address = address
            if latitude:
                customer.latitude = latitude
            if longitude:
                customer.longitude = longitude

            customer.updated_at = datetime.utcnow()
            await db.commit()
            await db.refresh(customer)
            return customer

        except Exception as e:
            logger.error(f"Error updating customer: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def save_conversation(
            db: AsyncSession,
            customer_id: int,
            role: str,
            message: str,
            prompt_sent: Optional[str] = None,
            tokens_input: Optional[int] = None,
            tokens_output: Optional[int] = None,
            cost_pkr: Optional[float] = None
    ):
        """Save conversation to database with optional prompt and token info"""
        try:
            conversation = ConversationHistory(
                customer_id=customer_id,
                role=role,
                message=message,
                prompt_sent=prompt_sent,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                cost_pkr=cost_pkr
            )
            db.add(conversation)
            await db.commit()
        except Exception as e:
            logger.error(f"Error saving conversation: {e}")
            await db.rollback()

    @staticmethod
    async def get_recent_conversations(
            db: AsyncSession,
            customer_id: int,
            limit: int = 50
    ) -> List[ConversationHistory]:
        """Get recent conversations for a customer"""
        try:
            result = await db.execute(
                select(ConversationHistory)
                .where(ConversationHistory.customer_id == customer_id)
                .order_by(ConversationHistory.created_at.desc())
                .limit(limit)
            )
            return list(reversed(result.scalars().all()))
        except Exception as e:
            logger.error(f"Error getting conversations: {e}")
            return []

    @staticmethod
    async def get_last_order(db: AsyncSession, customer_id: int) -> Optional[Order]:
        """Get customer's most recent order"""
        try:
            result = await db.execute(
                select(Order)
                .where(Order.customer_id == customer_id)
                .order_by(Order.created_at.desc())
                .limit(1)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting last order: {e}")
            return None


customer_service = CustomerService()
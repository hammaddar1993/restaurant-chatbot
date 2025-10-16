from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database_models import Reservation
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReservationService:
    @staticmethod
    async def create_reservation(
            db: AsyncSession,
            customer_id: int,
            reservation_date: datetime,
            number_of_people: int,
            special_requests: str = None
    ) -> Reservation:
        """Create a new table reservation"""
        try:
            reservation = Reservation(
                customer_id=customer_id,
                reservation_date=reservation_date,
                number_of_people=number_of_people,
                special_requests=special_requests,
                status="pending"
            )

            db.add(reservation)
            await db.commit()
            await db.refresh(reservation)
            logger.info(f"Created reservation {reservation.id} for customer {customer_id}")
            return reservation

        except Exception as e:
            logger.error(f"Error creating reservation: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_reservation_status(
            db: AsyncSession,
            reservation_id: int,
            status: str
    ):
        """Update reservation status"""
        try:
            reservation = await db.get(Reservation, reservation_id)

            if reservation:
                reservation.status = status
                await db.commit()
        except Exception as e:
            logger.error(f"Error updating reservation: {e}")
            await db.rollback()


reservation_service = ReservationService()
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database_models import Complaint
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ComplaintService:
    @staticmethod
    async def create_complaint(
            db: AsyncSession,
            customer_id: int,
            description: str
    ) -> Complaint:
        """Create a new complaint"""
        try:
            complaint = Complaint(
                customer_id=customer_id,
                description=description,
                status="open"
            )

            db.add(complaint)
            await db.commit()
            await db.refresh(complaint)
            logger.info(f"Created complaint {complaint.id} for customer {customer_id}")
            return complaint

        except Exception as e:
            logger.error(f"Error creating complaint: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_complaint_status(
            db: AsyncSession,
            complaint_id: int,
            status: str,
            resolution: Optional[str] = None
    ):
        """Update complaint status"""
        try:
            complaint = await db.get(Complaint, complaint_id)

            if complaint:
                complaint.status = status
                if resolution:
                    complaint.resolution = resolution
                if status == "resolved":
                    complaint.resolved_at = datetime.utcnow()

                await db.commit()
        except Exception as e:
            logger.error(f"Error updating complaint: {e}")
            await db.rollback()


complaint_service = ComplaintService()
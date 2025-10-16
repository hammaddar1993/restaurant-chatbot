from fastapi import FastAPI, Request, Response, Depends
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
import logging

from app.core.config import settings
from app.core.database import init_db, get_session
from app.routes import webhook
from app.services.redis_service import redis_client
from app.services.cost_tracking_service import cost_tracking_service
from app.services.gemini_service import gemini_service
from app.models.database_models import ConversationHistory, Customer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("Starting up application...")
    await init_db()
    await redis_client.connect()
    await cost_tracking_service.connect()
    logger.info("Application started successfully")

    yield

    # Shutdown
    logger.info("Shutting down application...")
    await redis_client.close()
    logger.info("Application shut down successfully")


app = FastAPI(
    title="Restaurant WhatsApp Chatbot",
    description="AI-powered WhatsApp chatbot for restaurant operations",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(webhook.router, prefix="/webhook", tags=["webhook"])


@app.get("/")
async def root():
    return {"message": "Restaurant WhatsApp Chatbot API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/admin/costs/daily")
async def get_daily_costs():
    """Get today's LLM costs"""
    stats = await cost_tracking_service.get_daily_stats()
    return stats


@app.get("/admin/costs/monthly")
async def get_monthly_costs():
    """Get this month's LLM costs"""
    stats = await cost_tracking_service.get_monthly_stats()
    return stats


@app.post("/admin/reload-prompt")
async def reload_prompt():
    """Reload system prompt and restaurant info from files"""
    try:
        gemini_service.reload_prompt()
        return {
            "status": "success",
            "message": "System prompt and restaurant info reloaded successfully"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@app.get("/admin/restaurant-info")
async def get_restaurant_info():
    """Get current restaurant information"""
    return gemini_service.get_restaurant_info()


@app.get("/admin/conversations/{phone_number}")
async def get_conversations(
        phone_number: str,
        limit: int = 10,
        db: AsyncSession = Depends(get_session)
):
    """Get conversation history for a phone number"""
    try:
        # Get customer
        result = await db.execute(
            select(Customer).where(Customer.phone_number == phone_number)
        )
        customer = result.scalar_one_or_none()

        if not customer:
            return {"error": "Customer not found"}

        # Get conversations
        result = await db.execute(
            select(ConversationHistory)
            .where(ConversationHistory.customer_id == customer.id)
            .order_by(desc(ConversationHistory.created_at))
            .limit(limit)
        )
        conversations = list(reversed(result.scalars().all()))

        return {
            "customer": {
                "phone": customer.phone_number,
                "name": customer.name,
                "id": customer.id
            },
            "conversations": [
                {
                    "id": conv.id,
                    "role": conv.role,
                    "message": conv.message,
                    "prompt_sent": conv.prompt_sent if conv.role == "assistant" else None,
                    "tokens_input": conv.tokens_input,
                    "tokens_output": conv.tokens_output,
                    "cost_pkr": conv.cost_pkr,
                    "created_at": conv.created_at.isoformat()
                }
                for conv in conversations
            ]
        }
    except Exception as e:
        return {"error": str(e)}


@app.get("/admin/customers")
async def list_customers(db: AsyncSession = Depends(get_session)):
    """List all customers"""
    try:
        result = await db.execute(select(Customer))
        customers = result.scalars().all()

        return {
            "customers": [
                {
                    "id": c.id,
                    "phone": c.phone_number,
                    "name": c.name,
                    "created_at": c.created_at.isoformat()
                }
                for c in customers
            ]
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
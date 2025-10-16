from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_session
from app.services.redis_service import redis_client
from app.services.whatsapp_service import whatsapp_service
from app.services.gemini_service import gemini_service
from app.services.customer_service import customer_service
from app.services.order_service import order_service
from app.services.complaint_service import complaint_service
from app.services.reservation_service import reservation_service
from app.services.cost_tracking_service import cost_tracking_service
from app.models.database_models import OrderType, OrderStatus
from datetime import datetime
import logging
import json
import hashlib

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/")
async def verify_webhook(request: Request):
    """Verify WhatsApp webhook"""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == settings.WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return PlainTextResponse(challenge)

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/")
async def handle_webhook(
        request: Request,
        db: AsyncSession = Depends(get_session)
):
    """Handle incoming WhatsApp messages"""
    try:
        body = await request.json()
        logger.info(f"Received webhook: {json.dumps(body)}")

        # Extract message data
        if not body.get("entry"):
            return {"status": "ok"}

        for entry in body["entry"]:
            for change in entry.get("changes", []):
                value = change.get("value", {})
                messages = value.get("messages", [])

                for message in messages:
                    await process_message(message, db)

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Error handling webhook: {e}")
        return {"status": "error", "message": str(e)}


async def process_message(message: dict, db: AsyncSession):
    """Process individual WhatsApp message"""
    try:
        phone_number = message.get("from")
        message_id = message.get("id")
        message_type = message.get("type")

        logger.info(f"=" * 80)
        logger.info(f"📱 NEW MESSAGE RECEIVED")
        logger.info(f"From: {phone_number}")
        logger.info(f"Message ID: {message_id}")
        logger.info(f"Type: {message_type}")
        logger.info(f"=" * 80)

        # Mark message as read
        await whatsapp_service.mark_as_read(message_id)
        logger.info(f"✓ Message marked as read")

        # Get or create customer
        customer = await customer_service.get_or_create_customer(db, phone_number)
        logger.info(f"👤 Customer: {customer.name or 'New Customer'} (ID: {customer.id})")

        # Extract message text
        user_message = ""
        if message_type == "text":
            user_message = message.get("text", {}).get("body", "")
            logger.info(f"💬 User Message: '{user_message}'")
        elif message_type == "location":
            location = message.get("location", {})
            latitude = location.get("latitude")
            longitude = location.get("longitude")

            logger.info(f"📍 Location Received: {latitude}, {longitude}")

            # Update customer location
            await customer_service.update_customer_info(
                db, customer.id,
                latitude=latitude,
                longitude=longitude
            )

            # Update session
            await redis_client.update_session(phone_number, {
                "pending_location": False,
                "location": {"latitude": latitude, "longitude": longitude}
            })

            user_message = f"[Location shared: {latitude}, {longitude}]"
            logger.info(f"✓ Customer location updated")
        else:
            logger.info(f"⚠️ Unsupported message type: {message_type}")
            return

        # Add to conversation history (Redis and DB)
        await redis_client.add_to_conversation(phone_number, "user", user_message)
        await customer_service.save_conversation(db, customer.id, "user", user_message)
        logger.info(f"✓ Message saved to conversation history")

        # Get session context
        session = await redis_client.get_session(phone_number) or {}
        conversation_history = await redis_client.get_conversation_history(phone_number)
        logger.info(f"💾 Session Context: {len(conversation_history)} messages in history")

        # Get menu items for context - ALWAYS fetch fresh menu
        menu_items = await order_service.get_menu_items(db)
        menu_text = order_service.format_menu_for_ai(menu_items)

        # Log menu availability for debugging
        logger.info(f"📋 Menu loaded: {len(menu_items)} items")
        logger.info(f"📋 Menu text length: {len(menu_text)} characters")
        logger.info(f"📋 Menu preview (first 200 chars): {menu_text[:200]}...")

        # Check if we should request feedback for last order
        last_order = await customer_service.get_last_order(db, customer.id)
        if last_order and await order_service.should_request_feedback(last_order):
            logger.info(f"⭐ Feedback due for order #{last_order.id}")
            session["should_request_feedback"] = True
            session["last_order"] = {
                "id": last_order.id,
                "items": json.loads(last_order.items),
                "total": last_order.total_price,
                "completed_at": last_order.completed_at.isoformat()
            }

        logger.info(f"🤖 Generating AI response...")
        logger.info(f"🤖 Context being sent to AI: {list(session.keys())}")

        # Generate AI response
        ai_response, input_tokens, output_tokens, full_prompt = await gemini_service.generate_response(
            user_message,
            conversation_history,
            session,
            menu_text
        )

        # Calculate cost
        cost_usd = ((input_tokens / 1_000_000) * 0.075) + ((output_tokens / 1_000_000) * 0.30)
        cost_pkr = cost_usd * 280

        # Track costs
        await cost_tracking_service.track_usage(input_tokens, output_tokens, phone_number)

        logger.info(f"🤖 AI Response received (length: {len(ai_response)} chars)")
        logger.info(f"🤖 AI Response preview: {ai_response[:300]}...")

        # Extract and process actions
        action = gemini_service.extract_action(ai_response)
        if action:
            logger.info(f"⚡ Action detected: {action.get('type')}")
            logger.info(f"⚡ Action data: {json.dumps(action.get('data', {}), indent=2)}")
            await handle_action(action, customer, db, phone_number, session)
        else:
            logger.info(f"ℹ️ No action detected in response")

        # Get clean response text
        clean_response = gemini_service.get_clean_response(ai_response)

        # Validate response is not empty
        if not clean_response or len(clean_response.strip()) < 5:
            logger.error(f"❌ AI response is empty or too short")
            logger.error(f"Original response: {ai_response[:500]}")
            clean_response = "I'm having trouble responding right now. Please try again."

        logger.info(f"📤 Sending response to customer: '{clean_response[:200]}...'")

        # Send response
        success = await whatsapp_service.send_text_message(phone_number, clean_response)
        if success:
            logger.info(f"✅ Message sent successfully")
        else:
            logger.error(f"❌ Failed to send message")

        # Add assistant response to conversation
        await redis_client.add_to_conversation(phone_number, "assistant", clean_response)
        await customer_service.save_conversation(
            db,
            customer.id,
            "assistant",
            clean_response,
            prompt_sent=full_prompt,
            tokens_input=input_tokens,
            tokens_output=output_tokens,
            cost_pkr=cost_pkr
        )
        logger.info(f"✓ Assistant response saved to history with prompt and token info")

        logger.info(f"=" * 80)
        logger.info(f"✅ MESSAGE PROCESSING COMPLETE")
        logger.info(f"=" * 80)

    except Exception as e:
        logger.error(f"❌ ERROR processing message: {str(e)}")
        logger.exception(e)
        await whatsapp_service.send_text_message(
            phone_number,
            "I apologize, but I encountered an error processing your request. Please try again."
        )


async def handle_action(action: dict, customer, db: AsyncSession, phone_number: str, session: dict):
    """Handle structured actions from AI"""
    try:
        action_type = action.get("type")
        data = action.get("data", {})

        logger.info(f"⚡ Processing action: {action_type}")
        logger.info(f"⚡ Action data: {json.dumps(data, indent=2)}")

        if action_type == "create_order":
            logger.info(f"🛒 Creating order...")
            # Create order
            order_type = OrderType(data.get("order_type", "dine_in"))
            items = data.get("items", [])
            total_price = data.get("total_price", 0)

            logger.info(f"🛒 Order type: {order_type}")
            logger.info(f"🛒 Items: {items}")
            logger.info(f"🛒 Total: Rs. {total_price}")

            delivery_address = None
            delivery_lat = None
            delivery_lon = None

            if order_type == OrderType.DELIVERY:
                delivery_address = data.get("address") or customer.address
                location = session.get("location", {})
                delivery_lat = location.get("latitude") or customer.latitude
                delivery_lon = location.get("longitude") or customer.longitude
                logger.info(f"🚚 Delivery address: {delivery_address}")
                logger.info(f"🚚 Delivery location: {delivery_lat}, {delivery_lon}")

            order = await order_service.create_order(
                db, customer.id, order_type, items, total_price,
                delivery_address, delivery_lat, delivery_lon
            )

            logger.info(f"✅ Order created successfully: Order #{order.id}")

            # Update session
            await redis_client.update_session(phone_number, {
                "current_order": None,
                "last_order": {
                    "id": order.id,
                    "items": items,
                    "total": total_price,
                    "type": order_type.value,
                    "created_at": order.created_at.isoformat()
                }
            })
            logger.info(f"✅ Session updated with order info")

        elif action_type == "create_complaint":
            logger.info(f"⚠️ Creating complaint...")
            # Create complaint
            description = data.get("description", "")
            complaint = await complaint_service.create_complaint(db, customer.id, description)
            logger.info(f"✅ Complaint created: #{complaint.id}")

        elif action_type == "create_reservation":
            logger.info(f"📅 Creating reservation...")
            # Create reservation
            reservation_date_str = data.get("reservation_date")
            reservation_date = datetime.fromisoformat(reservation_date_str)
            number_of_people = data.get("number_of_people", 2)
            special_requests = data.get("special_requests")

            logger.info(f"📅 Date: {reservation_date}")
            logger.info(f"📅 People: {number_of_people}")
            logger.info(f"📅 Special requests: {special_requests}")

            reservation = await reservation_service.create_reservation(
                db, customer.id, reservation_date,
                number_of_people, special_requests
            )
            logger.info(f"✅ Reservation created: #{reservation.id}")

        elif action_type == "update_customer_info":
            logger.info(f"👤 Updating customer info...")
            # Update customer info
            name = data.get("name")
            address = data.get("address")

            logger.info(f"👤 Name: {name}")
            logger.info(f"👤 Address: {address}")

            await customer_service.update_customer_info(
                db, customer.id,
                name=name,
                address=address
            )
            logger.info(f"✅ Customer info updated")

        elif action_type == "save_feedback":
            logger.info(f"⭐ Saving feedback...")
            # Save order feedback
            order_id = data.get("order_id")
            feedback = data.get("feedback")

            if order_id and feedback:
                await order_service.save_feedback(db, order_id, feedback)
                await redis_client.update_session(phone_number, {
                    "should_request_feedback": False
                })
                logger.info(f"✅ Feedback saved for order #{order_id}")

        logger.info(f"✅ Action processed successfully")

    except Exception as e:
        logger.error(f"❌ Error handling action: {e}")
        logger.exception(e)
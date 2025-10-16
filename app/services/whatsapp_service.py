import aiohttp
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class WhatsAppService:
    def __init__(self):
        self.api_url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
        self.headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json"
        }

    async def send_text_message(self, to: str, message: str) -> bool:
        """Send text message via WhatsApp Cloud API"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": False,
                    "body": message
                }
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Message sent successfully to {to}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send message: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return False

    async def send_image_message(self, to: str, image_url: str, caption: Optional[str] = None) -> bool:
        """Send image message via WhatsApp Cloud API"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "image",
                "image": {
                    "link": image_url
                }
            }

            if caption:
                payload["image"]["caption"] = caption

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                ) as response:
                    if response.status == 200:
                        logger.info(f"Image sent successfully to {to}")
                        return True
                    else:
                        error_text = await response.text()
                        logger.error(f"Failed to send image: {error_text}")
                        return False
        except Exception as e:
            logger.error(f"Error sending image: {e}")
            return False

    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read"""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }

            async with aiohttp.ClientSession() as session:
                async with session.post(
                        self.api_url,
                        headers=self.headers,
                        json=payload
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False


# Singleton instance
whatsapp_service = WhatsAppService()
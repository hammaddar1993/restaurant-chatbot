import google.generativeai as genai
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
import logging
import json
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class GeminiService:
    def __init__(self):
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)
        self.system_prompt = self._load_system_prompt()
        self.restaurant_info = self._load_restaurant_info()

    def _load_system_prompt(self) -> str:
        """Load system prompt from file"""
        try:
            prompt_file = Path(__file__).parent.parent.parent / "prompts" / "system_prompt.txt"
            if prompt_file.exists():
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    prompt = f.read()
                logger.info(f"✓ System prompt loaded from file ({len(prompt)} chars)")
                return prompt
            else:
                logger.warning(f"Prompt file not found: {prompt_file}")
                return self._build_default_prompt()
        except Exception as e:
            logger.error(f"Error loading prompt file: {e}")
            return self._build_default_prompt()

    def _load_restaurant_info(self) -> Dict:
        """Load restaurant info from JSON file"""
        try:
            config_file = Path(__file__).parent.parent.parent / "config" / "restaurant_info.json"
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    info = json.load(f)
                logger.info(f"✓ Restaurant info loaded from file")
                return info
            else:
                logger.warning(f"Config file not found: {config_file}")
                return {}
        except Exception as e:
            logger.error(f"Error loading restaurant info: {e}")
            return {}

    def _build_default_prompt(self) -> str:
        """Fallback default prompt if file not found"""
        return """You are a waiter at DUMx Broast Restaurant taking orders via WhatsApp.

Keep responses SHORT and natural like a real waiter. Maximum 2-3 sentences.

Restaurant: DUMx Broast Restaurant
Location: Johar Town, Lahore
Phone: 0304 1113869
Hours: 12 PM - 3 AM

Be brief, friendly, and efficient like a real waiter."""

    def reload_prompt(self):
        """Reload system prompt and restaurant info from files"""
        self.system_prompt = self._load_system_prompt()
        self.restaurant_info = self._load_restaurant_info()
        logger.info("✓ Prompt and restaurant info reloaded")

    def get_restaurant_info(self, key: str = None):
        """Get restaurant information"""
        if key:
            return self.restaurant_info.get(key)
        return self.restaurant_info

    async def generate_response(
            self,
            user_message: str,
            conversation_history: List[Dict[str, str]],
            context: Dict[str, Any],
            menu_items: Optional[str] = None
    ) -> Tuple[str, int, int, str]:
        """Generate AI response using Gemini

        Returns:
            tuple: (response_text, input_tokens, output_tokens, full_prompt)
        """
        try:
            logger.info(f"🤖 AI Generation Starting...")
            logger.info(f"🤖 System Prompt (first 200 chars): {self.system_prompt[:200]}...")

            # Build context string
            context_str = self._build_context_string(context, menu_items)
            logger.info(f"🤖 Context string length: {len(context_str)} characters")

            # Build conversation for Gemini
            full_prompt = f"""{self.system_prompt}

**CONTEXT INFORMATION**:
{context_str}

**CONVERSATION HISTORY**:
"""
            # Add recent conversation history
            for msg in conversation_history[-10:]:  # Last 10 messages for context
                role = "Customer" if msg["role"] == "user" else "Assistant"
                full_prompt += f"{role}: {msg['message']}\n"

            full_prompt += f"\nCustomer: {user_message}\nAssistant:"

            # Calculate input tokens (rough estimate: ~4 chars per token)
            input_tokens = len(full_prompt) // 4

            logger.info(f"🤖 Full prompt length: {len(full_prompt)} characters")
            logger.info(f"🤖 Estimated input tokens: {input_tokens}")
            logger.info(f"🤖 Calling Gemini API...")

            # Generate response
            response = await self.model.generate_content_async(full_prompt)

            # Calculate output tokens
            output_tokens = len(response.text) // 4
            total_tokens = input_tokens + output_tokens

            # Calculate cost (Gemini Flash pricing as of 2024)
            # Input: $0.075 per 1M tokens
            # Output: $0.30 per 1M tokens
            # USD to PKR: ~280 (approximate)
            input_cost_usd = (input_tokens / 1_000_000) * 0.075
            output_cost_usd = (output_tokens / 1_000_000) * 0.30
            total_cost_usd = input_cost_usd + output_cost_usd
            total_cost_pkr = total_cost_usd * 280

            logger.info(f"🤖 Gemini API response received")
            logger.info(f"📊 TOKEN USAGE:")
            logger.info(f"   Input tokens:  {input_tokens:,}")
            logger.info(f"   Output tokens: {output_tokens:,}")
            logger.info(f"   Total tokens:  {total_tokens:,}")
            logger.info(f"💰 COST BREAKDOWN:")
            logger.info(f"   Input cost:  ${input_cost_usd:.6f} (Rs. {input_cost_usd * 280:.4f})")
            logger.info(f"   Output cost: ${output_cost_usd:.6f} (Rs. {output_cost_usd * 280:.4f})")
            logger.info(f"   Total cost:  ${total_cost_usd:.6f} (Rs. {total_cost_pkr:.4f})")
            logger.info(f"🤖 Response text length: {len(response.text)} characters")
            logger.info(f"🤖 Response: {response.text}")

            return response.text, input_tokens, output_tokens, full_prompt

        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            logger.exception(e)
            return "Sorry, something went wrong. Try again?", 0, 0, ""

    def _build_context_string(self, context: Dict[str, Any], menu_items: Optional[str]) -> str:
        """Build context string from session data"""
        context_parts = []

        # Add menu first and prominently
        if menu_items:
            context_parts.append("=" * 50)
            context_parts.append("RESTAURANT MENU (USE THIS TO ANSWER QUESTIONS)")
            context_parts.append("=" * 50)
            context_parts.append(menu_items)
            context_parts.append("=" * 50)
            context_parts.append("")

        if context.get("customer_name"):
            context_parts.append(f"Customer Name: {context['customer_name']}")

        if context.get("current_order"):
            context_parts.append(f"Current Order in Progress: {json.dumps(context['current_order'])}")

        if context.get("last_order"):
            context_parts.append(f"Last Order: {json.dumps(context['last_order'])}")

        if context.get("pending_address"):
            context_parts.append("Waiting for: Customer address for delivery order")

        if context.get("pending_location"):
            context_parts.append("Waiting for: Customer location coordinates")

        return "\n".join(context_parts) if context_parts else "No additional context"

    def extract_action(self, response: str) -> Optional[Dict[str, Any]]:
        """Extract action JSON from response using regex"""
        try:
            # Match ```action { ... } ``` or ```json { ... } ```
            pattern = r"```(?:action|json)\s*(\{[\s\S]*?\})\s*```"
            match = re.search(pattern, response)
            if match:
                action_str = match.group(1).strip()
                try:
                    return json.loads(action_str)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error in action block: {e}")
                    logger.debug(f"Raw action text: {action_str[:300]}")
                    return None
            return None
        except Exception as e:
            logger.error(f"Error extracting action: {e}")
            return None

    def get_clean_response(self, response: str) -> str:
        """Remove any ```action or ```json blocks and return user-friendly text"""
        try:
            # Remove all action/json code blocks
            clean = re.sub(r"```(?:action|json)[\s\S]*?```", "", response).strip()

            if not clean or len(clean) < 5:
                logger.warning("⚠️ Empty response after removing action block")
                logger.debug(f"Original response: {response[:300]}")
                return "I'll help you with that. How can I assist?"

            return clean
        except Exception as e:
            logger.error(f"Error cleaning response: {e}")
            return "I'll help you with that. How can I assist?"


# Singleton instance
gemini_service = GeminiService()
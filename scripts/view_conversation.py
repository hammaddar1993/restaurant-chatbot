"""
Script to view conversation details including prompts
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc
from app.models.database_models import ConversationHistory, Customer
from app.core.config import settings


async def view_conversations(phone_number: str = None, limit: int = 10):
    """View conversation history with prompt details"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        if phone_number:
            # Get specific customer
            result = await session.execute(
                select(Customer).where(Customer.phone_number == phone_number)
            )
            customer = result.scalar_one_or_none()

            if not customer:
                print(f"❌ No customer found with phone: {phone_number}")
                return

            # Get conversations
            result = await session.execute(
                select(ConversationHistory)
                .where(ConversationHistory.customer_id == customer.id)
                .order_by(desc(ConversationHistory.created_at))
                .limit(limit)
            )
            conversations = list(reversed(result.scalars().all()))

            print("\n" + "=" * 80)
            print(f"CONVERSATION HISTORY: {customer.name or phone_number}")
            print("=" * 80)

        else:
            # Get recent conversations
            result = await session.execute(
                select(ConversationHistory)
                .order_by(desc(ConversationHistory.created_at))
                .limit(limit)
            )
            conversations = list(reversed(result.scalars().all()))

            print("\n" + "=" * 80)
            print(f"RECENT CONVERSATIONS (Last {limit})")
            print("=" * 80)

        if not conversations:
            print("No conversations found")
            return

        total_cost = 0
        for i, conv in enumerate(conversations, 1):
            print(f"\n{'─' * 80}")
            print(f"Message #{i} | {conv.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'─' * 80}")
            print(f"Role: {conv.role.upper()}")
            print(f"Message: {conv.message}")

            if conv.role == "assistant":
                print(f"\n📊 TOKEN INFO:")
                if conv.tokens_input:
                    print(f"   Input Tokens: {conv.tokens_input:,}")
                if conv.tokens_output:
                    print(f"   Output Tokens: {conv.tokens_output:,}")
                if conv.tokens_input and conv.tokens_output:
                    print(f"   Total Tokens: {conv.tokens_input + conv.tokens_output:,}")
                if conv.cost_pkr:
                    print(f"   Cost: Rs. {conv.cost_pkr:.4f}")
                    total_cost += conv.cost_pkr

                if conv.prompt_sent:
                    print(f"\n📝 FULL PROMPT SENT TO GEMINI:")
                    print(f"{'─' * 80}")
                    print(f"{conv.prompt_sent[:500]}...")
                    print(f"{'─' * 80}")
                    print(f"Full prompt length: {len(conv.prompt_sent)} characters")

                    # Save full prompt to file option
                    save = input("\n💾 Save full prompt to file? (y/n): ")
                    if save.lower() == 'y':
                        filename = f"prompt_{conv.id}_{conv.created_at.strftime('%Y%m%d_%H%M%S')}.txt"
                        with open(filename, 'w', encoding='utf-8') as f:
                            f.write(f"Conversation ID: {conv.id}\n")
                            f.write(f"Timestamp: {conv.created_at}\n")
                            f.write(f"Customer Message: {conversations[i - 2].message if i > 1 else 'N/A'}\n")
                            f.write(f"AI Response: {conv.message}\n")
                            f.write(f"\n{'=' * 80}\n")
                            f.write(f"FULL PROMPT:\n")
                            f.write(f"{'=' * 80}\n\n")
                            f.write(conv.prompt_sent)
                        print(f"✅ Saved to {filename}")

        if total_cost > 0:
            print(f"\n{'=' * 80}")
            print(f"💰 TOTAL COST FOR THIS CONVERSATION: Rs. {total_cost:.4f}")
            print(f"{'=' * 80}")

    await engine.dispose()


async def list_customers():
    """List all customers with conversation counts"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        result = await session.execute(select(Customer))
        customers = result.scalars().all()

        print("\n" + "=" * 80)
        print("CUSTOMERS")
        print("=" * 80)

        for customer in customers:
            # Count conversations
            result = await session.execute(
                select(ConversationHistory)
                .where(ConversationHistory.customer_id == customer.id)
            )
            conv_count = len(result.scalars().all())

            print(f"\n📱 {customer.phone_number}")
            print(f"   Name: {customer.name or 'N/A'}")
            print(f"   Messages: {conv_count}")
            print(f"   Joined: {customer.created_at.strftime('%Y-%m-%d')}")

    await engine.dispose()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            asyncio.run(list_customers())
        else:
            phone = sys.argv[1]
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            asyncio.run(view_conversations(phone, limit))
    else:
        print("Usage:")
        print("  python scripts/view_conversation.py list                    - List all customers")
        print("  python scripts/view_conversation.py <phone>                 - View customer conversations")
        print("  python scripts/view_conversation.py <phone> <limit>         - View last N messages")
        print("\nExamples:")
        print("  python scripts/view_conversation.py +923001234567")
        print("  python scripts/view_conversation.py +923001234567 20")
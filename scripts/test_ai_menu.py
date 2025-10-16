"""
Test script to verify AI can access and understand the menu
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.services.gemini_service import gemini_service
from app.services.order_service import order_service
from app.core.config import settings


async def test_ai_menu_knowledge():
    """Test if AI can see and respond about menu items"""

    print("\n" + "=" * 60)
    print("Testing AI Menu Knowledge")
    print("=" * 60 + "\n")

    # Get menu items
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        menu_items = await order_service.get_menu_items(session)
        menu_text = order_service.format_menu_for_ai(menu_items)

        print(f"✓ Loaded {len(menu_items)} menu items")
        print(f"✓ Menu text length: {len(menu_text)} characters\n")

        # Test questions
        test_questions = [
            "What burgers do you have?",
            "How much is a Quarter Broast?",
            "Tell me about your deals",
            "What beverages are available?",
            "I want to order a Full Broast, how much will it cost?"
        ]

        print("Testing AI responses to menu questions:\n")
        print("-" * 60 + "\n")

        for i, question in enumerate(test_questions, 1):
            print(f"Question {i}: {question}")
            print("-" * 40)

            try:
                # Generate AI response with menu context
                response = await gemini_service.generate_response(
                    user_message=question,
                    conversation_history=[],
                    context={},
                    menu_items=menu_text
                )

                # Clean the response
                clean_response = gemini_service.get_clean_response(response)

                print(f"AI Response: {clean_response}\n")

            except Exception as e:
                print(f"❌ Error: {e}\n")

        print("=" * 60)
        print("✅ AI Menu Knowledge Test Complete!")
        print("=" * 60 + "\n")

    await engine.dispose()


if __name__ == "__main__":
    # Note: You need a valid Gemini API key in .env for this to work
    print("\n⚠️  Make sure you have a valid GEMINI_API_KEY in your .env file")
    print("Get one from: https://aistudio.google.com/app/apikey\n")

    try:
        asyncio.run(test_ai_menu_knowledge())
    except Exception as e:
        print(f"\n❌ Error running test: {e}")
        print("\nMake sure:")
        print("1. You have a valid GEMINI_API_KEY in .env")
        print("2. Database is running (docker-compose up -d)")
        print("3. Menu is initialized (python scripts/init_menu.py)")
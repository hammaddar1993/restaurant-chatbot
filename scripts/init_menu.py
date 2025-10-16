"""
Script to initialize the menu items in the database.
Run this after the database is created.
"""
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from app.models.database_models import MenuItem
from app.core.config import settings

# Menu data
MENU_DATA = [
    {"category": "Deals", "item_name": "4x4", "price": 2326.72, "price_with_tax": 2700, "description": "4 Spicy Thigh, 4 Spicy Leg, 3 Dips, 2 Buns & 1.5 Litre Soft Drink", "options": "Served With Fries", "synonyms": "3 Dip Broast Deals", "serving": 4},
    {"category": "Deals", "item_name": "BIG FAT PARTY", "price": 8793.1, "price_with_tax": 10200, "description": "16 Spicy Thigh, 16 Spicy Leg, 10 Dips, 8 Buns & 3 Soft Drink 1.5 Litre", "options": "Served With Fries", "synonyms": "10 Dip Broast Deals", "serving": 16},
    {"category": "Deals", "item_name": "Hot Duos", "price": 1250, "price_with_tax": 1450, "description": "2 Spicy Thigh, 2 Spicy Leg, 2 Dips, 1 Bun & 1 Soft Drink", "options": "Served With Fries", "synonyms": "2 Dip Broast Deals", "serving": 2},
    {"category": "Deals", "item_name": "Spicy Singles", "price": 818.97, "price_with_tax": 950, "description": "1 Spicy Thigh, 1 Spicy Leg, 1 Dip, 1 Bun & 1 Soft Drink", "options": "Served With Fries", "synonyms": "1 Dip Broast Deals", "serving": 1},
    {"category": "Deals", "item_name": "Crispy & Spicy", "price": 1033.62, "price_with_tax": 1200, "description": "1 DUMx Burger, 1 Spicy Leg, 1 Dip & 1 Soft Drink", "options": "Served With Fries", "synonyms": "1 DIp Broast Deals", "serving": 1},
    {"category": "Deals", "item_name": "Ultimate Family", "price": 4568.97, "price_with_tax": 5300, "description": "8 Spicy Thigh, 8 Spicy Leg, 6 Dips, 4 Buns & 2 Soft Drink 1.5 Litre", "options": "Served With Fries", "synonyms": "6 Dip Broast Deals", "serving": 8},
    {"category": "Broast", "item_name": "Quarter Broast", "price": 732.76, "price_with_tax": 850, "description": "1 Spicy Thigh, 1 Spicy Leg,", "options": "Served With Bun, Fries & Dip", "synonyms": "1 Dip Broast", "serving": 1},
    {"category": "Broast", "item_name": "Half Broast", "price": 1206.03, "price_with_tax": 1400, "description": "2 Spicy Thigh, 2 Spicy Leg,", "options": "Served With Bun, Fries & Dip", "synonyms": "1 Dip Broast", "serving": 2},
    {"category": "Broast", "item_name": "Full Broast", "price": 2240.52, "price_with_tax": 2600, "description": "4 Spicy Thigh, 4 Spicy Leg,", "options": "Served With Bun, Fries & Dip", "synonyms": "1 Dip Broast", "serving": 4},
    {"category": "Burgers", "item_name": "Chicken Burger", "price": 758.62, "price_with_tax": 880, "description": None, "options": None, "synonyms": None, "serving": 1},
    {"category": "Burgers", "item_name": "DUMX Burger", "price": 775, "price_with_tax": 900, "description": None, "options": None, "synonyms": None, "serving": 1},
    {"category": "Wraps", "item_name": "Tortilla Wrap", "price": 646.55, "price_with_tax": 750, "description": None, "options": None, "synonyms": None, "serving": 1},
    {"category": "Wings", "item_name": "BBQ Wings", "price": 688.79, "price_with_tax": 800, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Wings", "item_name": "Hot Wings", "price": 688.79, "price_with_tax": 800, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Wings", "item_name": "Sweet Chili Wings", "price": 688.79, "price_with_tax": 800, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Sides", "item_name": "Nuggets", "price": 430.17, "price_with_tax": 500, "description": None, "options": None, "synonyms": "Fries, Add ons, Starters", "serving": 0.5},
    {"category": "Sides", "item_name": "Regular Fries", "price": 301.72, "price_with_tax": 350, "description": None, "options": None, "synonyms": "small fries", "serving": 0.5},
    {"category": "Sides", "item_name": "Large Fries", "price": 430.17, "price_with_tax": 500, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Sides", "item_name": "Masala Fries", "price": 430.17, "price_with_tax": 500, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Sides", "item_name": "Curly Fries", "price": 560.34, "price_with_tax": 650, "description": None, "options": None, "synonyms": None, "serving": 0.5},
    {"category": "Sides", "item_name": "Loaded Fries", "price": 602.59, "price_with_tax": 700, "description": None, "options": None, "synonyms": None, "serving": 1},
    {"category": "Extra", "item_name": "Bun", "price": 43.1, "price_with_tax": 50, "description": None, "options": None, "synonyms": "Extra Bun", "serving": 0},
    {"category": "Extra", "item_name": "Cheese Slice", "price": 77.59, "price_with_tax": 90, "description": None, "options": None, "synonyms": "Extra Cheese", "serving": 0},
    {"category": "Dips", "item_name": "Chipotle Dips", "price": 129.31, "price_with_tax": 150, "description": None, "options": None, "synonyms": "Sauce", "serving": 0},
    {"category": "Dips", "item_name": "Honey Mustard Dip", "price": 129.31, "price_with_tax": 150, "description": None, "options": None, "synonyms": "Sauce", "serving": 0},
    {"category": "Dips", "item_name": "Garlic Dip", "price": 129.31, "price_with_tax": 150, "description": None, "options": None, "synonyms": "Sauce", "serving": 0},
    {"category": "Water", "item_name": "Mineral Water small", "price": 86.21, "price_with_tax": 100, "description": None, "options": None, "synonyms": "small water", "serving": 0},
    {"category": "Water", "item_name": "Mineral Water large", "price": 129.31, "price_with_tax": 150, "description": None, "options": None, "synonyms": "large water", "serving": 0},
    {"category": "Beverages", "item_name": "Soft Drink small", "price": 86.21, "price_with_tax": 100, "description": None, "options": None, "synonyms": "Drink, Coke, Pepsi, Sprint, Mint", "serving": 0},
    {"category": "Beverages", "item_name": "Soft Drink half liter", "price": 103.45, "price_with_tax": 120, "description": None, "options": None, "synonyms": "Drink, Coke, Pepsi, Sprint, Mint", "serving": 0},
    {"category": "Beverages", "item_name": "Soft Drink one liter", "price": 198.28, "price_with_tax": 230, "description": None, "options": None, "synonyms": None, "serving": 0},
    {"category": "Beverages", "item_name": "Blue Lagoon", "price": 301.72, "price_with_tax": 350, "description": None, "options": None, "synonyms": None, "serving": 0},
    {"category": "Beverages", "item_name": "Peach Ice Tea", "price": 258.62, "price_with_tax": 300, "description": None, "options": None, "synonyms": "Peach,", "serving": 0},
    {"category": "Beverages", "item_name": "Strawberry Chiller", "price": 301.72, "price_with_tax": 350, "description": None, "options": None, "synonyms": "Stawberry, chiller", "serving": 0},
    {"category": "Beverages", "item_name": "Peach Chiller", "price": 301.72, "price_with_tax": 350, "description": None, "options": None, "synonyms": "Peach, chiller", "serving": 0},
    {"category": "Beverages", "item_name": "Lychee chiller", "price": 301.72, "price_with_tax": 350, "description": None, "options": None, "synonyms": "Lychee, chiller", "serving": 0},
    {"category": "Beverages", "item_name": "Mint Margarita", "price": 343.96, "price_with_tax": 400, "description": None, "options": None, "synonyms": "Mint, chiller", "serving": 0},
]

async def init_menu():
    """Initialize menu items in database"""
    engine = create_async_engine(settings.DATABASE_URL, echo=True)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with async_session() as session:
        # Check if menu already exists
        from sqlalchemy import select
        result = await session.execute(select(MenuItem))
        existing_items = result.scalars().all()

        if existing_items:
            print(f"Menu already initialized with {len(existing_items)} items")
            return

        # Add all menu items
        for item_data in MENU_DATA:
            menu_item = MenuItem(**item_data)
            session.add(menu_item)

        await session.commit()
        print(f"Successfully initialized {len(MENU_DATA)} menu items")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_menu())
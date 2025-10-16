"""
Script to view LLM API costs
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
from app.services.cost_tracking_service import cost_tracking_service
from app.core.config import settings
from datetime import datetime, timedelta


async def view_costs():
    """Display LLM cost statistics"""
    await cost_tracking_service.connect()

    print("\n" + "=" * 60)
    print("LLM API COST TRACKER - DUMx Broast Restaurant")
    print("=" * 60)

    # Today's costs
    print("\n📊 TODAY'S USAGE:")
    print("-" * 60)
    today_stats = await cost_tracking_service.get_daily_stats()
    if today_stats:
        print(f"Date: {today_stats['date']}")
        print(f"Total Requests: {today_stats['requests']:,}")
        print(f"Input Tokens: {today_stats['input_tokens']:,}")
        print(f"Output Tokens: {today_stats['output_tokens']:,}")
        print(f"Total Tokens: {today_stats['total_tokens']:,}")
        print(f"Cost (USD): ${today_stats['cost_usd']:.6f}")
        print(f"Cost (PKR): Rs. {today_stats['cost_pkr']:.2f}")
        if today_stats['requests'] > 0:
            avg_cost = today_stats['cost_pkr'] / today_stats['requests']
            print(f"Avg Cost/Request: Rs. {avg_cost:.4f}")
    else:
        print("No usage data for today")

    # This month's costs
    print("\n📊 THIS MONTH'S USAGE:")
    print("-" * 60)
    month_stats = await cost_tracking_service.get_monthly_stats()
    if month_stats:
        print(f"Month: {month_stats['month']}")
        print(f"Total Requests: {month_stats['requests']:,}")
        print(f"Input Tokens: {month_stats['input_tokens']:,}")
        print(f"Output Tokens: {month_stats['output_tokens']:,}")
        print(f"Total Tokens: {month_stats['total_tokens']:,}")
        print(f"Cost (USD): ${month_stats['cost_usd']:.6f}")
        print(f"Cost (PKR): Rs. {month_stats['cost_pkr']:.2f}")
        print(f"Avg Cost/Request: Rs. {month_stats['avg_cost_per_request_pkr']:.4f}")

        # Projections
        days_in_month = 30
        current_day = datetime.now().day
        if current_day > 0:
            projected_monthly = (month_stats['cost_pkr'] / current_day) * days_in_month
            print(f"\n💡 Projected Month End: Rs. {projected_monthly:.2f}")
    else:
        print("No usage data for this month")

    # Cost breakdown
    print("\n💰 PRICING INFO:")
    print("-" * 60)
    print("Model: Gemini 2.0 Flash")
    print("Input: $0.075 per 1M tokens")
    print("Output: $0.30 per 1M tokens")
    print("Exchange Rate: 1 USD = 280 PKR (approx)")

    # Estimations
    print("\n📈 COST ESTIMATES:")
    print("-" * 60)
    print("1,000 messages: ~Rs. 50-100")
    print("10,000 messages: ~Rs. 500-1,000")
    print("100,000 messages: ~Rs. 5,000-10,000")

    print("\n" + "=" * 60)
    print("✅ Cost tracking complete!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(view_costs())
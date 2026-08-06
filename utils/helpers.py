import math
from datetime import datetime, date
from typing import Union, Any


def round_to_tick(price: float, tick_size: float = 0.05) -> float:
    """
    Rounds a stock or derivative price to the nearest exchange tick size (e.g., 0.05).
    """
    if price <= 0:
        return 0.0
    return round(math.round(price / tick_size) * tick_size, 2) if hasattr(math, 'round') else round(round(price / tick_size) * tick_size, 2)


def format_currency(amount: float) -> str:
    """
    Formats float numeric values into INR currency standard format.
    """
    return f"₹{amount:,.2f}"


def parse_datetime(dt_str: Union[str, datetime]) -> datetime:
    """
    Parses ISO strings or returns datetime objects directly.
    """
    if isinstance(dt_str, datetime):
        return dt_str
    try:
        return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    except ValueError:
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")


def is_market_open() -> bool:
    """
    Checks if current system time falls within standard Indian Equity Market Hours (9:15 AM - 3:30 PM, Mon-Fri).
    """
    now = datetime.now()
    if now.weekday() >= 5:  # Saturday or Sunday
        return False

    start_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    end_time = now.replace(hour=15, minute=30, second=0, microsecond=0)

    return start_time <= now <= end_time

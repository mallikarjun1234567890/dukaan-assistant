"""Shop-local clock. Gemini must not invent the current time."""

from datetime import datetime

from app.models import Shop
from app.timeutil import shop_zone

WEEKDAYS = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


def shop_now(shop: Shop) -> datetime:
    return datetime.now(shop_zone(shop.timezone or "Asia/Kolkata"))


def is_open(shop: Shop, at: datetime | None = None) -> bool:
    current = at or shop_now(shop)
    weekday = current.strftime("%A")
    if shop.weekly_off and shop.weekly_off.strip().lower() == weekday.lower():
        return False
    try:
        open_h, open_m = [int(part) for part in (shop.opens_at or "09:00").split(":")]
        close_h, close_m = [int(part) for part in (shop.closes_at or "21:30").split(":")]
    except ValueError:
        return True
    minutes = current.hour * 60 + current.minute
    start = open_h * 60 + open_m
    end = close_h * 60 + close_m
    if end <= start:
        return minutes >= start or minutes < end
    return start <= minutes < end


def shop_clock(shop: Shop) -> dict[str, str | bool]:
    current = shop_now(shop)
    return {
        "timezone": shop.timezone or "Asia/Kolkata",
        "local_time": current.strftime("%Y-%m-%d %H:%M"),
        "weekday": current.strftime("%A"),
        "opens_at": shop.opens_at or "09:00",
        "closes_at": shop.closes_at or "21:30",
        "weekly_off": shop.weekly_off or "",
        "is_open": is_open(shop, current),
    }

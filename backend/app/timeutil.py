"""Shop-local calendar helpers."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def shop_zone(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError:
        return ZoneInfo("UTC")


def today_utc_bounds(timezone_name: str) -> tuple[datetime, datetime]:
    start_local = datetime.now(shop_zone(timezone_name)).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    start = start_local.astimezone(ZoneInfo("UTC"))
    return start, start + timedelta(days=1)

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo


def calculate_first_checkin(checkin_time: str, timezone_name: str) -> datetime:
    """
    Calculate the next occurrence of the user's configured check-in time.

    Example:
        checkin_time = "08:00"
        timezone = "Africa/Cairo"

    If current time is before 08:00:
        return today at 08:00

    If current time is after 08:00:
        return tomorrow at 08:00.
    """

    tz = ZoneInfo(timezone_name)

    now = datetime.now(tz)

    hour, minute = map(int, checkin_time.split(":"))

    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0,)

    if scheduled <= now:
        scheduled += timedelta(days=1)

    return scheduled.astimezone(ZoneInfo("UTC"))
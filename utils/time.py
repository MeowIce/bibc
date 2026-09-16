from datetime import datetime, timezone, timedelta

def utcNow() -> datetime:
    return datetime.now(timezone.utc)

def startOfUtcWeek(now: datetime | None = None) -> datetime:
    if now is None:
        now = utcNow()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
    
    startOfDay = now.replace(hour=0, minute=0, second=0, microsecond=0)
    return startOfDay - timedelta(days=startOfDay.weekday())

def startOfUtcMonth(now: datetime | None = None) -> datetime:
    if now is None:
        now = utcNow()
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    else:
        now = now.astimezone(timezone.utc)
        
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

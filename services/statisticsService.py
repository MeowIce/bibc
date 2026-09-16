from datetime import datetime
from repositories.banRepository import BanRepository
from utils.time import startOfUtcWeek, startOfUtcMonth

class StatisticsService:
    def __init__(self, repository: BanRepository):
        self.repository = repository

    def countThisWeek(self, guildId: int | None = None, now: datetime | None = None) -> int:
        weekStart = startOfUtcWeek(now)
        return self.repository.countSince(weekStart, guildId=guildId, action="banned")

    def countThisMonth(self, guildId: int | None = None, now: datetime | None = None) -> int:
        monthStart = startOfUtcMonth(now)
        return self.repository.countSince(monthStart, guildId=guildId, action="banned")

    def countTotal(self, guildId: int | None = None) -> int:
        return self.repository.countTotal(guildId=guildId, action="banned")

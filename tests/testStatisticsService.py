from datetime import datetime, timezone
import pytest
from database import Database
from models.banRecord import BanRecord

try:
    from repositories.banRepository import BanRepository
    from services.statisticsService import StatisticsService
    from utils.time import startOfUtcWeek, startOfUtcMonth
except ImportError:
    BanRepository = None
    StatisticsService = None
    startOfUtcWeek = None
    startOfUtcMonth = None

def testTimeWindowHelpers():
    assert startOfUtcWeek is not None
    assert startOfUtcMonth is not None
    
    ref = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    weekStart = startOfUtcWeek(ref)
    assert weekStart == datetime(2026, 9, 7, 0, 0, 0, tzinfo=timezone.utc)
    assert weekStart.weekday() == 0
    
    monthStart = startOfUtcMonth(ref)
    assert monthStart == datetime(2026, 9, 1, 0, 0, 0, tzinfo=timezone.utc)

def testStatisticsServiceCounts(tmp_path):
    assert StatisticsService is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = BanRepository(db)
    service = StatisticsService(repo)
    
    tInMonth = datetime(2026, 9, 2, 10, 0, 0, tzinfo=timezone.utc)
    tInWeek = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
    tPriorMonth = datetime(2026, 8, 25, 10, 0, 0, tzinfo=timezone.utc)
    
    repo.insert(BanRecord(guildId=1, userId=1, username="u1", channelId=1, messageId=1, policy="enforced", action="banned", reason="s", createdAt=tInMonth))
    repo.insert(BanRecord(guildId=1, userId=2, username="u2", channelId=1, messageId=2, policy="enforced", action="banned", reason="s", createdAt=tInWeek))
    repo.insert(BanRecord(guildId=1, userId=3, username="u3", channelId=1, messageId=3, policy="enforced", action="banned", reason="s", createdAt=tPriorMonth))
    repo.insert(BanRecord(guildId=1, userId=4, username="u4", channelId=1, messageId=4, policy="permissive", action="detected", reason="s", createdAt=tInWeek))
    
    nowRef = datetime(2026, 9, 13, 12, 0, 0, tzinfo=timezone.utc)
    
    weekCount = service.countThisWeek(guildId=1, now=nowRef)
    assert weekCount == 1
    
    monthCount = service.countThisMonth(guildId=1, now=nowRef)
    assert monthCount == 2
    
    totalCount = service.countTotal(guildId=1)
    assert totalCount == 3
    
    db.close()

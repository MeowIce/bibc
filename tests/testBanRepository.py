from datetime import datetime, timezone
import pytest
from database import Database
from models.banRecord import BanRecord

try:
    from repositories.banRepository import BanRepository
except ImportError:
    BanRepository = None

def testBanRepositoryInsertAndCount(tmp_path):
    assert BanRepository is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = BanRepository(db)
    
    t1 = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 12, 10, 0, 0, tzinfo=timezone.utc)
    
    rec1 = BanRecord(guildId=1, userId=100, username="user1", channelId=10, messageId=101, policy="enforced", action="banned", reason="spam", createdAt=t1)
    rec2 = BanRecord(guildId=1, userId=101, username="user2", channelId=10, messageId=102, policy="enforced", action="banned", reason="spam", createdAt=t2)
    rec3 = BanRecord(guildId=2, userId=102, username="user3", channelId=20, messageId=103, policy="enforced", action="banned", reason="spam", createdAt=t2)
    recDetected = BanRecord(guildId=1, userId=103, username="user4", channelId=10, messageId=104, policy="permissive", action="detected", reason="spam", createdAt=t2)
    
    saved1 = repo.insert(rec1)
    assert saved1.id is not None
    repo.insert(rec2)
    repo.insert(rec3)
    repo.insert(recDetected)
    
    countAllBanned = repo.countSince(t1)
    assert countAllBanned == 3
    
    countGuild1Banned = repo.countSince(t1, guildId=1)
    assert countGuild1Banned == 2
    
    countAfterT1 = repo.countSince(datetime(2026, 9, 11, 0, 0, 0, tzinfo=timezone.utc), guildId=1)
    assert countAfterT1 == 1
    
    db.close()

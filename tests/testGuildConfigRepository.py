import pytest
from database import Database

try:
    from repositories.guildConfigRepository import GuildConfigRepository
except ImportError:
    GuildConfigRepository = None

def testRepositoryGetMissingReturnsNone(tmp_path):
    assert GuildConfigRepository is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = GuildConfigRepository(db)
    
    config = repo.get(99999)
    assert config is None
    db.close()

def testRepositoryUpsertWatchChannel(tmp_path):
    assert GuildConfigRepository is not None
    dbPath = str(tmp_path / "test.db")
    db = Database(dbPath)
    db.initialize()
    repo = GuildConfigRepository(db)
    
    cfg = repo.upsertWatchChannel(guildId=123, channelId=456)
    assert cfg.guildId == 123
    assert cfg.watchChannelId == 456
    assert cfg.policy == "enforced"
    
    updated = repo.upsertWatchChannel(guildId=123, channelId=789)
    assert updated.watchChannelId == 789
    
    db.close()
    
    reopenedDb = Database(dbPath)
    reopenedRepo = GuildConfigRepository(reopenedDb)
    persisted = reopenedRepo.get(123)
    assert persisted is not None
    assert persisted.watchChannelId == 789
    reopenedDb.close()

def testRepositoryUpdatePolicy(tmp_path):
    assert GuildConfigRepository is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = GuildConfigRepository(db)
    
    repo.upsertWatchChannel(guildId=123, channelId=456)
    cfgPerm = repo.updatePolicy(guildId=123, policy="permissive")
    assert cfgPerm.policy == "permissive"
    
    cfgEnf = repo.updatePolicy(guildId=123, policy="enforced")
    assert cfgEnf.policy == "enforced"
    
    with pytest.raises(ValueError):
        repo.updatePolicy(guildId=123, policy="bad_policy")
    
    db.close()

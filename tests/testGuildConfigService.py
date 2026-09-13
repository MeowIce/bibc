import pytest
from database import Database
from repositories.guildConfigRepository import GuildConfigRepository

try:
    from services.guildConfigService import GuildConfigService
except ImportError:
    GuildConfigService = None

def testServiceValidation(tmp_path):
    assert GuildConfigService is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = GuildConfigRepository(db)
    service = GuildConfigService(repo)
    
    with pytest.raises(ValueError, match="channel"):
        service.setWatchChannel(guildId=123, channelId=-1)
        
    with pytest.raises(ValueError, match="guild"):
        service.setWatchChannel(guildId=0, channelId=456)
        
    with pytest.raises(ValueError, match="policy"):
        service.setPolicy(guildId=123, policy="invalid")
        
    db.close()

def testServiceOperations(tmp_path):
    assert GuildConfigService is not None
    db = Database(str(tmp_path / "test.db"))
    db.initialize()
    repo = GuildConfigRepository(db)
    service = GuildConfigService(repo)
    
    cfg = service.setWatchChannel(guildId=123, channelId=456)
    assert cfg.watchChannelId == 456
    
    cfg = service.setPolicy(guildId=123, policy="permissive")
    assert cfg.policy == "permissive"
    
    retrieved = service.getConfig(guildId=123)
    assert retrieved is not None
    assert retrieved.policy == "permissive"
    assert retrieved.watchChannelId == 456
    
    db.close()

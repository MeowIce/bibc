import sqlite3
import pytest

try:
    from database import Database
    from models.guildConfig import GuildConfig
    from models.banRecord import BanRecord
except ImportError:
    Database = None
    GuildConfig = None
    BanRecord = None

def testDatabaseInitialization(tmp_path):
    assert Database is not None
    dbPath = str(tmp_path / "test.db")
    db = Database(dbPath)
    db.initialize()
    
    conn = sqlite3.connect(dbPath)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {row[0] for row in cursor.fetchall()}
    assert "guild_configs" in tables
    assert "ban_records" in tables
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}
    assert any("guild_configs" in idx or "ban_records" in idx for idx in indexes)
    
    conn.close()
    db.close()

def testDatabaseIdempotentInitialization(tmp_path):
    assert Database is not None
    dbPath = str(tmp_path / "test.db")
    db = Database(dbPath)
    db.initialize()
    db.initialize()
    db.close()

def testGuildConfigModelValidation():
    assert GuildConfig is not None
    cfg = GuildConfig(guildId=123, watchChannelId=456, policy="enforced")
    assert cfg.policy == "enforced"
    
    cfgPerm = GuildConfig(guildId=123, watchChannelId=456, policy="permissive")
    assert cfgPerm.policy == "permissive"
    
    with pytest.raises(ValueError, match="policy"):
        GuildConfig(guildId=123, watchChannelId=456, policy="invalid_policy")

def testBanRecordModel():
    assert BanRecord is not None
    record = BanRecord(
        guildId=123,
        userId=456,
        username="spammer#1234",
        channelId=789,
        messageId=101112,
        policy="enforced",
        action="banned",
        reason="gửi tin nhắn vào kênh lọc spam"
    )
    assert record.guildId == 123
    assert record.action == "banned"

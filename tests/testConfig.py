import pytest

try:
    from config import loadConfig, AppConfig
except ImportError:
    loadConfig = None
    AppConfig = None

def testLoadConfigSuccess(monkeypatch, tmp_path):
    assert loadConfig is not None
    dbPath = str(tmp_path / "test.db")
    monkeypatch.setenv("DISCORD_TOKEN", "fake_token_12345")
    monkeypatch.setenv("DATABASE_PATH", dbPath)
    
    cfg = loadConfig(loadEnv=False)
    assert isinstance(cfg, AppConfig)
    assert cfg.discordToken == "fake_token_12345"
    assert cfg.databasePath == dbPath

def testLoadConfigMissingTokenRaises(monkeypatch):
    assert loadConfig is not None
    monkeypatch.delenv("DISCORD_TOKEN", raising=False)
    
    with pytest.raises(ValueError, match="DISCORD_TOKEN"):
        loadConfig(loadEnv=False)

def testLoadConfigDefaultDatabasePath(monkeypatch):
    assert loadConfig is not None
    monkeypatch.setenv("DISCORD_TOKEN", "fake_token_12345")
    monkeypatch.delenv("DATABASE_PATH", raising=False)
    
    cfg = loadConfig(loadEnv=False)
    assert cfg.databasePath == "./data/bibc.db"

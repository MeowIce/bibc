import pytest
from unittest.mock import AsyncMock, MagicMock
from config import AppConfig

try:
    from bot import BibcBot
except ImportError:
    BibcBot = None

@pytest.mark.asyncio
async def testBotLifecycle(tmp_path):
    assert BibcBot is not None
    dbPath = str(tmp_path / "lifecycle.db")
    config = AppConfig(discordToken="fake_token", databasePath=dbPath)
    
    bot = BibcBot(config)
    bot.tree.sync = AsyncMock()
    
    assert bot.database is not None
    assert bot.guildConfigService is not None
    assert bot.banService is not None
    
    await bot.setup_hook()
    bot.tree.sync.assert_awaited_once()
    
    assert "config" in [cog.lower() for cog in bot.cogs]
    assert "statuscog" in [cog.lower() for cog in bot.cogs]
    
    await bot.close()
    assert bot.database._connection is None

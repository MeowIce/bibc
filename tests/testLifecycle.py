import discord
from discord import app_commands
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

@pytest.mark.asyncio
async def testOnReadyClearsGuildCommands(tmp_path, monkeypatch):
    assert BibcBot is not None
    dbPath = str(tmp_path / "lifecycle2.db")
    config = AppConfig(discordToken="fake_token", databasePath=dbPath)
    
    bot = BibcBot(config)
    bot.tree.clear_commands = MagicMock()
    bot.tree.sync = AsyncMock()
    bot.change_presence = AsyncMock()
    
    mockGuild = MagicMock()
    mockGuild.id = 12345
    mockGuild.member_count = 10
    monkeypatch.setattr(type(bot), "guilds", property(lambda self: [mockGuild]))
    mockUser = MagicMock()
    mockUser.id = 999
    mockUser.__str__ = lambda self: "TestBot#1234"
    monkeypatch.setattr(type(bot), "user", property(lambda self: mockUser))
    
    await bot.on_ready()
    
    bot.tree.clear_commands.assert_called_once_with(guild=mockGuild)
    bot.tree.sync.assert_awaited_once_with(guild=mockGuild)

@pytest.mark.asyncio
async def testCommandTreeNotFoundHandler(tmp_path):
    assert BibcBot is not None
    dbPath = str(tmp_path / "lifecycle3.db")
    config = AppConfig(discordToken="fake_token", databasePath=dbPath)
    
    bot = BibcBot(config)
    
    interaction = MagicMock()
    interaction.user.id = 777
    interaction.response.is_done.return_value = False
    interaction.response.send_message = AsyncMock()
    
    error = app_commands.CommandNotFound("avatar", [])
    await bot.tree.on_error(interaction, error)
    
    interaction.response.send_message.assert_awaited_once()
    assert "lỗi thời" in interaction.response.send_message.call_args[0][0]

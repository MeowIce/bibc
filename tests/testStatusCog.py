import discord
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

try:
    from cogs.status import formatActivityString, StatusCog, calculateMemberCount, updateBotStatus, getMinimalBotInviteUrl
except ImportError:
    formatActivityString = None
    StatusCog = None
    calculateMemberCount = None
    updateBotStatus = None
    getMinimalBotInviteUrl = None

def testFormatActivityString():
    assert formatActivityString is not None
    result = formatActivityString(serverCount=5, memberCount=250, bannedCount=12)
    assert result == "5 servers, 250 members, banned 12 accounts"

def testCalculateMemberCount():
    assert calculateMemberCount is not None
    guild1 = MagicMock()
    guild1.member_count = 100
    guild2 = MagicMock()
    guild2.member_count = 150
    assert calculateMemberCount([guild1, guild2]) == 250

@pytest.mark.asyncio
async def testUpdateBotStatus():
    assert updateBotStatus is not None
    bot = MagicMock()
    bot.change_presence = AsyncMock()
    guild1 = MagicMock()
    guild1.member_count = 100
    guild2 = MagicMock()
    guild2.member_count = 150
    bot.guilds = [guild1, guild2]
    bot.statisticsService = MagicMock()
    bot.statisticsService.countTotal.return_value = 8
    
    await updateBotStatus(bot)
    bot.change_presence.assert_awaited_once()
    activity = bot.change_presence.call_args.kwargs.get("activity")
    assert activity is not None
    assert activity.type == discord.ActivityType.watching
    assert activity.name == "2 servers, 250 members, banned 8 accounts"

@pytest.mark.asyncio
async def testStatusCommandOutput():
    assert StatusCog is not None
    interaction = MagicMock()
    interaction.guild_id = 12345
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    
    bot = MagicMock()
    bot.user.id = 993329384499208252
    guild1 = MagicMock()
    guild1.member_count = 100
    guild2 = MagicMock()
    guild2.member_count = 50
    bot.guilds = [guild1, guild2]
    
    statService = MagicMock()
    statService.countThisWeek.return_value = 2
    statService.countThisMonth.return_value = 5
    statService.countTotal.return_value = 10
    
    configService = MagicMock()
    cfg = MagicMock()
    cfg.policy = "enforced"
    configService.getConfig.return_value = cfg
    
    startTime = datetime.now(timezone.utc) - timedelta(days=1, hours=2, minutes=3, seconds=4)
    cog = StatusCog(bot=bot, statisticsService=statService, guildConfigService=configService, startTime=startTime)
    await cog.status.callback(cog, interaction)
    
    interaction.response.send_message.assert_awaited_once()
    view = interaction.response.send_message.call_args.kwargs.get("view")
    assert view is not None
    components = view.to_components()
    assert len(components) == 1
    assert components[0]["type"] == 17
    assert components[0].get("accent_color") is None
    
    containerComponents = components[0]["components"]
    contents = [c.get("content", "") for c in containerComponents if "content" in c]
    assert any("About BanInBlacklistedChannels Bot..." in c for c in contents)
    assert any("`993329384499208252`" in c for c in contents)
    assert any("`enforced`" in c for c in contents)
    assert any("10 / 5 / 2" in c for c in contents)
    assert any("Use the `/invite` command to get started !" in c for c in contents)

def testMinimalBotInviteUrl():
    assert getMinimalBotInviteUrl is not None
    url = getMinimalBotInviteUrl(993329384499208252)
    assert "client_id=993329384499208252" in url
    assert "scope=bot+applications.commands" in url
    assert "permissions=" in url

@pytest.mark.asyncio
async def testAboutCommandOutput():
    interaction = MagicMock()
    interaction.guild_id = 12345
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    
    bot = MagicMock()
    bot.user.id = 993329384499208252
    bot.guilds = []
    
    statService = MagicMock()
    statService.countThisWeek.return_value = 0
    statService.countThisMonth.return_value = 0
    statService.countTotal.return_value = 0
    
    configService = MagicMock()
    configService.getConfig.return_value = None
    
    startTime = datetime.now(timezone.utc)
    cog = StatusCog(bot=bot, statisticsService=statService, guildConfigService=configService, startTime=startTime)
    await cog.about.callback(cog, interaction)
    
    interaction.response.send_message.assert_awaited_once()
    view = interaction.response.send_message.call_args.kwargs.get("view")
    assert view is not None
    components = view.to_components()
    assert components[0].get("accent_color") is None

@pytest.mark.asyncio
async def testInviteCommandOutput():
    interaction = MagicMock()
    interaction.guild_id = 12345
    interaction.guild = MagicMock()
    interaction.response.send_message = AsyncMock()
    
    bot = MagicMock()
    bot.user.id = 993329384499208252
    
    statService = MagicMock()
    configService = MagicMock()
    cog = StatusCog(bot=bot, statisticsService=statService, guildConfigService=configService)
    await cog.invite.callback(cog, interaction)
    
    interaction.response.send_message.assert_awaited_once()
    kwargs = interaction.response.send_message.call_args.kwargs
    assert kwargs.get("ephemeral") is None or kwargs.get("ephemeral") is False
    view = kwargs.get("view")
    assert view is not None
    components = view.to_components()
    assert len(components) == 1
    assert components[0]["type"] == 17
    subComponents = components[0]["components"]
    textContents = [c.get("content", "") for c in subComponents if "content" in c]
    assert any("Invite BanInBlacklistedChannels Bot" in c for c in textContents)
    actionRow = next((c for c in subComponents if c.get("type") == 1), None)
    assert actionRow is not None
    buttonComponent = next((b for b in actionRow.get("components", []) if b.get("type") == 2 or "url" in b), None)
    assert buttonComponent is not None
    assert "993329384499208252" in buttonComponent.get("url", "")

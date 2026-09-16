from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
import pytest

try:
    from cogs.status import formatActivityString, StatusCog, calculateMemberCount
except ImportError:
    formatActivityString = None
    StatusCog = None
    calculateMemberCount = None

def testFormatActivityString():
    assert formatActivityString is not None
    result = formatActivityString(serverCount=5, memberCount=250)
    assert result == "Status type: watching, 5 servers - 250 members"

def testCalculateMemberCount():
    assert calculateMemberCount is not None
    guild1 = MagicMock()
    guild1.member_count = 100
    guild2 = MagicMock()
    guild2.member_count = 150
    assert calculateMemberCount([guild1, guild2]) == 250

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
    
    containerComponents = components[0]["components"]
    contents = [c.get("content", "") for c in containerComponents if "content" in c]
    assert any("About BanInBlacklistedChannels Bot..." in c for c in contents)
    assert any("`993329384499208252`" in c for c in contents)
    assert any("`enforced`" in c for c in contents)
    assert any("10 / 5 / 2" in c for c in contents)

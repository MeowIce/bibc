import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from cogs.status import formatActivityString, StatusCog
except ImportError:
    formatActivityString = None
    StatusCog = None

def testFormatActivityString():
    assert formatActivityString is not None
    result = formatActivityString(serverCount=5, memberCount=250)
    assert result == "Status type: watching, 5 servers - 250 members"

@pytest.mark.asyncio
async def testStatusCommandOutput():
    assert StatusCog is not None
    interaction = MagicMock()
    interaction.guild_id = 12345
    interaction.response.send_message = AsyncMock()
    
    bot = MagicMock()
    bot.user.id = 993329384499208252
    guild1 = MagicMock()
    guild1.member_count = 100
    guild2 = MagicMock()
    guild2.member_count = 50
    bot.guilds = [guild1, guild2]
    
    cog = StatusCog(bot, statisticsService=MagicMock(), guildConfigService=MagicMock())
    await cog.status.callback(cog, interaction)
    
    interaction.response.send_message.assert_awaited_once()
    embed = interaction.response.send_message.call_args.kwargs.get("embed")
    assert embed is not None

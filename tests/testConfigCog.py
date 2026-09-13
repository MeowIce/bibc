import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from cogs.config import ConfigCog
except ImportError:
    ConfigCog = None

@pytest.mark.asyncio
async def testConfigRequiresGuild():
    assert ConfigCog is not None
    interaction = MagicMock()
    interaction.guild_id = None
    interaction.guild = None
    interaction.response.send_message = AsyncMock()
    
    cog = ConfigCog(guildConfigService=MagicMock())
    await cog.watchchannel.callback(cog, interaction, channel=MagicMock())
    
    interaction.response.send_message.assert_awaited_once()
    assert "Server only" in interaction.response.send_message.call_args[0][0]

@pytest.mark.asyncio
async def testConfigRequiresAdmin():
    assert ConfigCog is not None
    interaction = MagicMock()
    interaction.guild_id = 12345
    interaction.guild = MagicMock()
    interaction.user.guild_permissions.administrator = False
    interaction.response.send_message = AsyncMock()
    
    cog = ConfigCog(guildConfigService=MagicMock())
    await cog.policy.callback(cog, interaction, policy="enforced")
    
    interaction.response.send_message.assert_awaited_once()
    assert "Administrator" in interaction.response.send_message.call_args[0][0]

from unittest.mock import AsyncMock, MagicMock
import discord
import pytest

try:
    from cogs.config import ConfigCog
except ImportError:
    ConfigCog = None

@pytest.fixture
def mockAdminInteraction():
    def createInteraction(guildId=12345, isAdmin=True):
        interaction = MagicMock()
        if guildId is None:
            interaction.guild_id = None
            interaction.guild = None
        else:
            interaction.guild_id = guildId
            interaction.guild = MagicMock()
            interaction.guild.id = guildId
        
        interaction.user = MagicMock()
        interaction.user.guild_permissions.administrator = isAdmin
        interaction.response.send_message = AsyncMock()
        return interaction
    return createInteraction

@pytest.mark.asyncio
async def testConfigRequiresGuild(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=None)
    
    cog = ConfigCog(guildConfigService=MagicMock())
    channel = MagicMock(spec=discord.TextChannel)
    channel.guild = MagicMock()
    await cog.watchchannel.callback(cog, interaction, channel=channel)
    
    interaction.response.send_message.assert_awaited_once()
    assert "Server only" in interaction.response.send_message.call_args[0][0]

@pytest.mark.asyncio
async def testConfigRequiresAdmin(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=12345, isAdmin=False)
    
    cog = ConfigCog(guildConfigService=MagicMock())
    await cog.policy.callback(cog, interaction, policy="enforced")
    
    interaction.response.send_message.assert_awaited_once()
    assert "Administrator" in interaction.response.send_message.call_args[0][0]

@pytest.mark.asyncio
async def testWatchChannelValidationMismatch(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=12345, isAdmin=True)
    
    channel = MagicMock(spec=discord.TextChannel)
    channel.guild = MagicMock()
    channel.guild.id = 99999
    channel.id = 55555
    channel.name = "other-channel"
    
    configService = MagicMock()
    cog = ConfigCog(guildConfigService=configService)
    await cog.watchchannel.callback(cog, interaction, channel=channel)
    
    interaction.response.send_message.assert_awaited_once()
    assert "current server" in interaction.response.send_message.call_args[0][0]
    configService.setWatchChannel.assert_not_called()

@pytest.mark.asyncio
async def testWatchChannelSuccess(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=12345, isAdmin=True)
    
    channel = MagicMock(spec=discord.TextChannel)
    channel.guild = interaction.guild
    channel.id = 55555
    channel.name = "spam-trap"
    
    configService = MagicMock()
    cog = ConfigCog(guildConfigService=configService)
    await cog.watchchannel.callback(cog, interaction, channel=channel)
    
    configService.setWatchChannel.assert_called_once_with(12345, 55555)
    interaction.response.send_message.assert_awaited_once()

@pytest.mark.asyncio
async def testPolicySuccess(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=12345, isAdmin=True)
    
    configService = MagicMock()
    cog = ConfigCog(guildConfigService=configService)
    await cog.policy.callback(cog, interaction, policy="permissive")
    
    configService.setPolicy.assert_called_once_with(12345, "permissive")
    interaction.response.send_message.assert_awaited_once()

@pytest.mark.asyncio
async def testPolicyInvalidRejected(mockAdminInteraction):
    assert ConfigCog is not None
    interaction = mockAdminInteraction(guildId=12345, isAdmin=True)
    
    configService = MagicMock()
    cog = ConfigCog(guildConfigService=configService)
    await cog.policy.callback(cog, interaction, policy="unknown")
    
    configService.setPolicy.assert_not_called()
    interaction.response.send_message.assert_awaited_once()

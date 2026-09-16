from datetime import datetime, timezone, timedelta
import discord
import pytest
from unittest.mock import AsyncMock, MagicMock
from models.guildConfig import GuildConfig
from models.banRecord import BanRecord

try:
    from services.banService import BanService, BanResult
except ImportError:
    BanService = None
    BanResult = None

@pytest.mark.asyncio
async def testBanServiceEnforcedSuccess(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="enforced")
    
    banRepo = MagicMock()
    service = BanService(banRepository=banRepo)
    result = await service.handleMessage(msg, guildConfig)
    
    assert isinstance(result, BanResult)
    assert result.action == "banned"
    msg.guild.ban.assert_awaited_once_with(
        msg.author,
        reason="gửi tin nhắn vào kênh lọc spam",
        delete_message_seconds=300
    )
    banRepo.insert.assert_called_once()
    savedRecord = banRepo.insert.call_args[0][0]
    assert savedRecord.action == "banned"

@pytest.mark.asyncio
async def testBanServicePermissive(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="permissive")
    
    banRepo = MagicMock()
    service = BanService(banRepository=banRepo)
    result = await service.handleMessage(msg, guildConfig)
    
    assert result.action == "detected"
    msg.guild.ban.assert_not_awaited()
    banRepo.insert.assert_called_once()
    savedRecord = banRepo.insert.call_args[0][0]
    assert savedRecord.action == "detected"

@pytest.mark.asyncio
async def testBanServiceForbiddenFailure(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    response = MagicMock()
    response.status = 403
    response.reason = "Forbidden"
    msg.guild.ban.side_effect = discord.Forbidden(response, "Missing Permissions")
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="enforced")
    
    banRepo = MagicMock()
    service = BanService(banRepository=banRepo)
    result = await service.handleMessage(msg, guildConfig)
    
    assert result.action == "failed"
    assert "Missing Permissions" in result.reason
    banRepo.insert.assert_called_once()
    savedRecord = banRepo.insert.call_args[0][0]
    assert savedRecord.action == "failed"

@pytest.mark.asyncio
async def testBanServiceHierarchySkip(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="enforced")
    
    msg.guild.owner_id = msg.author.id
    
    banRepo = MagicMock()
    service = BanService(banRepository=banRepo)
    result = await service.handleMessage(msg, guildConfig)
    
    assert result.action == "failed"
    msg.guild.ban.assert_not_awaited()

@pytest.mark.asyncio
async def testBanServiceDeleteMessageSecondsWithStartTime(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="enforced")
    
    banRepo = MagicMock()
    recentStartTime = datetime.now(timezone.utc) - timedelta(seconds=45)
    service = BanService(banRepository=banRepo, startTime=recentStartTime)
    result = await service.handleMessage(msg, guildConfig)
    
    assert result.action == "banned"
    calledArgs = msg.guild.ban.call_args
    assert calledArgs is not None
    deleteSeconds = calledArgs.kwargs["delete_message_seconds"]
    assert 40 <= deleteSeconds <= 50

@pytest.mark.asyncio
async def testBanServiceDeleteMessageSecondsCappedAt300(mockMessage):
    assert BanService is not None
    msg = mockMessage()
    guildConfig = GuildConfig(guildId=msg.guild.id, watchChannelId=msg.channel.id, policy="enforced")
    
    banRepo = MagicMock()
    oldStartTime = datetime.now(timezone.utc) - timedelta(hours=2)
    service = BanService(banRepository=banRepo, startTime=oldStartTime)
    result = await service.handleMessage(msg, guildConfig)
    
    assert result.action == "banned"
    calledArgs = msg.guild.ban.call_args
    assert calledArgs is not None
    assert calledArgs.kwargs["delete_message_seconds"] == 300

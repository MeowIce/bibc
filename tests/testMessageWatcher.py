import pytest
from unittest.mock import AsyncMock, MagicMock

try:
    from messageWatcher import handleMessageEvent
except ImportError:
    handleMessageEvent = None

@pytest.mark.asyncio
async def testWatchedChannelDetection(mockMessage):
    assert handleMessageEvent is not None
    watchedChannelId = 11111
    unrelatedChannelId = 22222
    
    watchedMsg = mockMessage(channelId=watchedChannelId)
    unrelatedMsg = mockMessage(channelId=unrelatedChannelId)
    
    handled = await handleMessageEvent(watchedMsg, watchedChannelId=watchedChannelId, policy="enforced")
    ignored = await handleMessageEvent(unrelatedMsg, watchedChannelId=watchedChannelId, policy="enforced")
    
    assert handled is True
    assert ignored is False

@pytest.mark.asyncio
async def testEnforcedPolicyBan(mockMessage):
    assert handleMessageEvent is not None
    channelId = 11111
    msg = mockMessage(channelId=channelId)
    
    await handleMessageEvent(msg, watchedChannelId=channelId, policy="enforced")
    
    msg.guild.ban.assert_awaited_once_with(
        msg.author,
        reason="gửi tin nhắn vào kênh lọc spam",
        delete_message_seconds=300
    )

@pytest.mark.asyncio
async def testPermissivePolicyNoBan(mockMessage):
    assert handleMessageEvent is not None
    channelId = 11111
    msg = mockMessage(channelId=channelId)
    
    await handleMessageEvent(msg, watchedChannelId=channelId, policy="permissive")
    
    msg.guild.ban.assert_not_awaited()

@pytest.mark.asyncio
async def testBotAuthorExcluded(mockMessage):
    assert handleMessageEvent is not None
    channelId = 11111
    msg = mockMessage(channelId=channelId, isBot=True)
    
    handled = await handleMessageEvent(msg, watchedChannelId=channelId, policy="enforced")
    
    assert handled is False
    msg.guild.ban.assert_not_awaited()

@pytest.mark.asyncio
async def testDmExcluded(mockMessage):
    assert handleMessageEvent is not None
    channelId = 11111
    msg = mockMessage(channelId=channelId, isDm=True)
    
    handled = await handleMessageEvent(msg, watchedChannelId=channelId, policy="enforced")
    
    assert handled is False

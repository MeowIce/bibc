import pytest
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mockUser():
    def createUser(userId=12345, name="testuser", isBot=False):
        user = MagicMock()
        user.id = userId
        user.name = name
        user.bot = isBot
        user.mention = f"<@{userId}>"
        user.__str__ = lambda self: name
        return user
    return createUser

@pytest.fixture
def mockGuild():
    def createGuild(guildId=99999, name="testguild"):
        guild = MagicMock()
        guild.id = guildId
        guild.name = name
        guild.ban = AsyncMock()
        channels = {}
        def getChannel(channelId):
            return channels.get(channelId)
        guild.get_channel = MagicMock(side_effect=getChannel)
        guild._channels = channels
        guild.member_count = 100
        guild.members = []
        return guild
    return createGuild

@pytest.fixture
def mockChannel():
    def createChannel(channelId=11111, name="test-channel", guild=None):
        channel = MagicMock()
        channel.id = channelId
        channel.name = name
        channel.guild = guild
        channel.send = AsyncMock()
        if guild is not None:
            guild._channels[channelId] = channel
        return channel
    return createChannel

@pytest.fixture
def mockMessage(mockUser, mockGuild, mockChannel):
    def createMessage(content="spam message", channelId=11111, guildId=99999, authorId=12345, isBot=False, isDm=False, attachments=None, stickers=None):
        message = MagicMock()
        message.id = 77777
        message.content = content
        message.attachments = attachments or []
        message.stickers = stickers or []
        message.delete = AsyncMock()
        author = mockUser(userId=authorId, name=f"user_{authorId}", isBot=isBot)
        message.author = author
        if isDm:
            message.guild = None
            message.channel = mockChannel(channelId=channelId, guild=None)
        else:
            guild = mockGuild(guildId=guildId)
            channel = mockChannel(channelId=channelId, guild=guild)
            message.guild = guild
            message.channel = channel
        return message
    return createMessage

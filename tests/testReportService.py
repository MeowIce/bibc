from unittest.mock import AsyncMock, MagicMock
import discord
import pytest
from models.guildConfig import GuildConfig
from services.reportService import ReportService

@pytest.fixture
def mockAttachment():
    def createAttachment(filename: str, url: str):
        att = MagicMock()
        att.filename = filename
        att.url = url
        return att
    return createAttachment

@pytest.fixture
def mockSticker():
    def createSticker(name: str, url: str):
        sticker = MagicMock()
        sticker.name = name
        sticker.url = url
        return sticker
    return createSticker

def testFormatMessageContentTextOnly(mockMessage):
    service = ReportService()
    msg = mockMessage(content="Hello world")
    assert service.formatMessageContent(msg) == "Hello world"

def testFormatMessageContentSingleAttachment(mockMessage, mockAttachment):
    service = ReportService()
    att = mockAttachment("photo.png", "https://cdn.discordapp.com/attachments/1/photo.png")
    msg = mockMessage(content="", attachments=[att])
    assert service.formatMessageContent(msg) == "[photo.png](https://cdn.discordapp.com/attachments/1/photo.png)"

def testFormatMessageContentAllMediaAttachments(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/attachments/1/photo.png")
    attVideo = mockAttachment("clip.mp4", "https://cdn.discordapp.com/attachments/2/clip.mp4")
    attAudio = mockAttachment("voice.mp3", "https://cdn.discordapp.com/attachments/3/voice.mp3")
    attDoc = mockAttachment("data.pdf", "https://cdn.discordapp.com/attachments/4/data.pdf")
    
    msg = mockMessage(content="", attachments=[attImage, attVideo, attAudio, attDoc])
    formatted = service.formatMessageContent(msg)
    
    assert "[photo.png](https://cdn.discordapp.com/attachments/1/photo.png)" in formatted
    assert "[clip.mp4](https://cdn.discordapp.com/attachments/2/clip.mp4)" in formatted
    assert "[voice.mp3](https://cdn.discordapp.com/attachments/3/voice.mp3)" in formatted
    assert "[data.pdf](https://cdn.discordapp.com/attachments/4/data.pdf)" in formatted

def testFormatMessageContentTextAndMultipleMedia(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("image.jpg", "https://cdn.discordapp.com/image.jpg")
    attVideo = mockAttachment("video.mp4", "https://cdn.discordapp.com/video.mp4")
    
    msg = mockMessage(content="spam message text", attachments=[attImage, attVideo])
    formatted = service.formatMessageContent(msg)
    
    assert formatted.startswith("spam message text")
    assert "[image.jpg](https://cdn.discordapp.com/image.jpg)" in formatted
    assert "[video.mp4](https://cdn.discordapp.com/video.mp4)" in formatted

def testFormatMessageContentStickers(mockMessage, mockSticker):
    service = ReportService()
    stk = mockSticker("customSticker", "https://cdn.discordapp.com/stickers/1.png")
    msg = mockMessage(content="", stickers=[stk])
    assert service.formatMessageContent(msg) == "[customSticker](https://cdn.discordapp.com/stickers/1.png)"

def testFormatMessageContentEmpty(mockMessage):
    service = ReportService()
    msg = mockMessage(content="")
    assert service.formatMessageContent(msg) == "<empty>"

def testFormatMessageContentTruncateOver1024(mockMessage, mockAttachment):
    service = ReportService(maxContentLength=800)
    attachments = [
        mockAttachment(f"file_{i}.dat", f"https://cdn.discordapp.com/attachments/test/{i}/very_long_file_name_path_item.dat")
        for i in range(20)
    ]
    msg = mockMessage(content="a" * 800, attachments=attachments)
    formatted = service.formatMessageContent(msg)
    assert len(formatted) <= 1024
    assert formatted.endswith("...")

@pytest.mark.asyncio
async def testSendEventReportNoReportChannel(mockMessage):
    service = ReportService()
    msg = mockMessage()
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=None)
    result = await service.sendEventReport(config, msg, "banned", "test reason")
    assert result is False

@pytest.mark.asyncio
async def testSendEventReportChannelNotFound(mockMessage):
    service = ReportService()
    msg = mockMessage()
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=999999)
    result = await service.sendEventReport(config, msg, "banned", "test reason")
    assert result is False

@pytest.mark.asyncio
async def testSendEventReportSuccessWithMultipleMedia(mockMessage, mockChannel, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/photo.png")
    attAudio = mockAttachment("voice.ogg", "https://cdn.discordapp.com/voice.ogg")
    
    msg = mockMessage(content="test content", attachments=[attImage, attAudio])
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "banned", "gửi tin nhắn vào kênh lọc spam")
    assert result is True
    reportCh.send.assert_awaited_once()
    
    embed = reportCh.send.call_args.kwargs.get("embed")
    assert embed is not None
    fieldDict = {f.name: f.value for f in embed.fields}
    assert fieldDict["Status"] == "Banned"
    assert "test content" in fieldDict["Message Content"]
    assert "[photo.png](https://cdn.discordapp.com/photo.png)" in fieldDict["Message Content"]
    assert "[voice.ogg](https://cdn.discordapp.com/voice.ogg)" in fieldDict["Message Content"]

@pytest.mark.asyncio
async def testSendEventReportDiscordExceptionHandling(mockMessage, mockChannel):
    service = ReportService()
    msg = mockMessage()
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    reportCh.send.side_effect = discord.HTTPException(MagicMock(status=500), "Server Error")
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "detected", "log only")
    assert result is False

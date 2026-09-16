from unittest.mock import AsyncMock, MagicMock
import discord
import pytest
from models.guildConfig import GuildConfig
from services.reportService import ReportService

@pytest.fixture
def mockAttachment():
    def createAttachment(filename: str, url: str, contentType: str = None):
        att = MagicMock()
        att.filename = filename
        att.url = url
        att.content_type = contentType
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

def testIsImageAttachment(mockAttachment):
    service = ReportService()
    pngAtt = mockAttachment("test.png", "https://cdn.discordapp.com/test.png")
    jpgAtt = mockAttachment("test.jpg", "https://cdn.discordapp.com/test.jpg")
    mimeAtt = mockAttachment("unknown", "https://cdn.discordapp.com/unknown", contentType="image/webp")
    videoAtt = mockAttachment("video.mp4", "https://cdn.discordapp.com/video.mp4", contentType="video/mp4")
    docAtt = mockAttachment("file.pdf", "https://cdn.discordapp.com/file.pdf")
    
    assert service.isImageAttachment(pngAtt) is True
    assert service.isImageAttachment(jpgAtt) is True
    assert service.isImageAttachment(mimeAtt) is True
    assert service.isImageAttachment(videoAtt) is False
    assert service.isImageAttachment(docAtt) is False

def testFormatMessageContentTextOnly(mockMessage):
    service = ReportService()
    msg = mockMessage(content="Hello world")
    assert service.formatMessageContent(msg) == "Hello world"

def testFormatMessageContentNonImageAttachment(mockMessage, mockAttachment):
    service = ReportService()
    att = mockAttachment("clip.mp4", "https://cdn.discordapp.com/attachments/1/clip.mp4")
    msg = mockMessage(content="", attachments=[att])
    assert service.formatMessageContent(msg) == "[clip.mp4](https://cdn.discordapp.com/attachments/1/clip.mp4)"

def testFormatMessageContentImageNotDuplicatedInText(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/attachments/1/photo.png")
    msg = mockMessage(content="caption text", attachments=[attImage])
    assert service.formatMessageContent(msg) == "caption text"

def testFormatMessageContentEmptyWithImageOnly(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/attachments/1/photo.png")
    msg = mockMessage(content="", attachments=[attImage])
    assert service.formatMessageContent(msg) == "<empty>"

def testFormatMessageContentAllMediaTypes(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/attachments/1/photo.png")
    attVideo = mockAttachment("clip.mp4", "https://cdn.discordapp.com/attachments/2/clip.mp4")
    attAudio = mockAttachment("voice.mp3", "https://cdn.discordapp.com/attachments/3/voice.mp3")
    attDoc = mockAttachment("data.pdf", "https://cdn.discordapp.com/attachments/4/data.pdf")
    
    msg = mockMessage(content="alert message", attachments=[attImage, attVideo, attAudio, attDoc])
    formatted = service.formatMessageContent(msg)
    
    assert "alert message" in formatted
    assert "[clip.mp4](https://cdn.discordapp.com/attachments/2/clip.mp4)" in formatted
    assert "[voice.mp3](https://cdn.discordapp.com/attachments/3/voice.mp3)" in formatted
    assert "[data.pdf](https://cdn.discordapp.com/attachments/4/data.pdf)" in formatted
    assert "[photo.png]" not in formatted

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

def testCreateReportEmbedsSingleImage(mockMessage, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/photo.png")
    msg = mockMessage(content="single image test", attachments=[attImage])
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    embeds = service.createReportEmbeds(config, msg, "banned", "reason")
    assert len(embeds) == 1
    assert embeds[0].image.url == "https://cdn.discordapp.com/photo.png"

def testCreateReportEmbedsMultipleImagesGallery(mockMessage, mockAttachment):
    service = ReportService()
    attImage1 = mockAttachment("photo1.png", "https://cdn.discordapp.com/photo1.png")
    attImage2 = mockAttachment("photo2.jpg", "https://cdn.discordapp.com/photo2.jpg")
    attImage3 = mockAttachment("photo3.webp", "https://cdn.discordapp.com/photo3.webp")
    msg = mockMessage(content="gallery test", attachments=[attImage1, attImage2, attImage3])
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    embeds = service.createReportEmbeds(config, msg, "banned", "reason")
    assert len(embeds) == 3
    assert embeds[0].image.url == "https://cdn.discordapp.com/photo1.png"
    assert embeds[1].image.url == "https://cdn.discordapp.com/photo2.jpg"
    assert embeds[2].image.url == "https://cdn.discordapp.com/photo3.webp"

def testCreateReportEmbedsSticker(mockMessage, mockSticker):
    service = ReportService()
    stk = mockSticker("customSticker", "https://cdn.discordapp.com/stickers/1.png")
    msg = mockMessage(content="", stickers=[stk])
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    embeds = service.createReportEmbeds(config, msg, "detected", "reason")
    assert len(embeds) == 1
    assert embeds[0].image.url == "https://cdn.discordapp.com/stickers/1.png"

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
async def testSendEventReportSuccessSingleEmbed(mockMessage, mockChannel, mockAttachment):
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
    assert embed.image.url == "https://cdn.discordapp.com/photo.png"
    fieldDict = {f.name: f.value for f in embed.fields}
    assert fieldDict["Status"] == "Banned"
    assert "test content" in fieldDict["Message Content"]
    assert "[voice.ogg](https://cdn.discordapp.com/voice.ogg)" in fieldDict["Message Content"]

@pytest.mark.asyncio
async def testSendEventReportSuccessMultipleEmbeds(mockMessage, mockChannel, mockAttachment):
    service = ReportService()
    attImage1 = mockAttachment("photo1.png", "https://cdn.discordapp.com/photo1.png")
    attImage2 = mockAttachment("photo2.png", "https://cdn.discordapp.com/photo2.png")
    
    msg = mockMessage(content="multi media", attachments=[attImage1, attImage2])
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "detected", "log only")
    assert result is True
    reportCh.send.assert_awaited_once()
    
    embeds = reportCh.send.call_args.kwargs.get("embeds")
    assert embeds is not None
    assert len(embeds) == 2
    assert embeds[0].image.url == "https://cdn.discordapp.com/photo1.png"
    assert embeds[1].image.url == "https://cdn.discordapp.com/photo2.png"

@pytest.mark.asyncio
async def testSendEventReportDiscordExceptionHandling(mockMessage, mockChannel):
    service = ReportService()
    msg = mockMessage()
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    reportCh.send.side_effect = discord.HTTPException(MagicMock(status=500), "Server Error")
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "detected", "log only")
    assert result is False

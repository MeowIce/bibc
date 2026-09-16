from unittest.mock import AsyncMock, MagicMock
import discord
import pytest
from models.guildConfig import GuildConfig
from services.reportService import ReportService, SavedMedia

@pytest.fixture
def mockAttachment():
    def createAttachment(filename: str, url: str, contentType: str = None, data: bytes = b"test data"):
        att = MagicMock()
        att.filename = filename
        att.url = url
        att.content_type = contentType
        att.read = AsyncMock(return_value=data)
        return att
    return createAttachment

@pytest.fixture
def mockSticker():
    def createSticker(name: str, url: str, data: bytes = b"sticker data"):
        sticker = MagicMock()
        sticker.name = name
        sticker.url = url
        sticker.read = AsyncMock(return_value=data)
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

@pytest.mark.asyncio
async def testCollectMediaFromAttachmentsAndStickers(mockMessage, mockAttachment, mockSticker):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/photo.png", data=b"img")
    attVideo = mockAttachment("clip.mp4", "https://cdn.discordapp.com/clip.mp4", data=b"vid")
    stk = mockSticker("custom", "https://cdn.discordapp.com/sticker.png", data=b"stk")
    
    msg = mockMessage(attachments=[attImage, attVideo], stickers=[stk])
    mediaList = await service.collectMedia(msg)
    
    assert len(mediaList) == 3
    assert mediaList[0].filename == "0_photo.png"
    assert mediaList[0].data == b"img"
    assert mediaList[0].isImage is True
    
    assert mediaList[1].filename == "1_clip.mp4"
    assert mediaList[1].data == b"vid"
    assert mediaList[1].isImage is False
    
    assert mediaList[2].filename == "sticker_0.png"
    assert mediaList[2].data == b"stk"
    assert mediaList[2].isImage is True

def testFormatMessageContentTextOnly(mockMessage):
    service = ReportService()
    msg = mockMessage(content="Hello world")
    assert service.formatMessageContent(msg) == "Hello world"

def testFormatMessageContentEmptyWithImageOnly(mockMessage):
    service = ReportService()
    msg = mockMessage(content="")
    media = [SavedMedia(filename="0_photo.png", data=b"img", isImage=True)]
    assert service.formatMessageContent(msg, media) == "<empty>"

def testFormatMessageContentWithNonImageMedia(mockMessage):
    service = ReportService()
    msg = mockMessage(content="spam text")
    media = [
        SavedMedia(filename="0_photo.png", data=b"img", isImage=True),
        SavedMedia(filename="1_video.mp4", data=b"vid", isImage=False)
    ]
    formatted = service.formatMessageContent(msg, media)
    assert "spam text" in formatted
    assert "Attached file: 1_video.mp4" in formatted
    assert "0_photo.png" not in formatted

def testFormatMessageContentTruncateOver1024(mockMessage):
    service = ReportService(maxContentLength=800)
    msg = mockMessage(content="a" * 800)
    media = [SavedMedia(filename=f"file_{i}.dat", data=b"1", isImage=False) for i in range(20)]
    formatted = service.formatMessageContent(msg, media)
    assert len(formatted) <= 1024
    assert formatted.endswith("...")

def testCreateReportEmbedsSingleImage(mockMessage):
    service = ReportService()
    msg = mockMessage(content="single image test")
    media = [SavedMedia(filename="0_photo.png", data=b"img", isImage=True)]
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    embeds = service.createReportEmbeds(config, msg, "banned", "reason", media)
    assert len(embeds) == 1
    assert embeds[0].image.url == "attachment://0_photo.png"

def testCreateReportEmbedsMultipleImagesGallery(mockMessage):
    service = ReportService()
    msg = mockMessage(content="gallery test")
    media = [
        SavedMedia(filename="0_photo1.png", data=b"img1", isImage=True),
        SavedMedia(filename="1_photo2.jpg", data=b"img2", isImage=True),
        SavedMedia(filename="2_photo3.webp", data=b"img3", isImage=True)
    ]
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    embeds = service.createReportEmbeds(config, msg, "banned", "reason", media)
    assert len(embeds) == 3
    assert embeds[0].image.url == "attachment://0_photo1.png"
    assert embeds[1].image.url == "attachment://1_photo2.jpg"
    assert embeds[2].image.url == "attachment://2_photo3.webp"

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
async def testSendEventReportSuccessWithReuploadedFiles(mockMessage, mockChannel, mockAttachment):
    service = ReportService()
    attImage = mockAttachment("photo.png", "https://cdn.discordapp.com/photo.png", data=b"imagebytes")
    attAudio = mockAttachment("voice.ogg", "https://cdn.discordapp.com/voice.ogg", data=b"audiobytes")
    
    msg = mockMessage(content="test content", attachments=[attImage, attAudio])
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "banned", "gửi tin nhắn vào kênh lọc spam")
    assert result is True
    reportCh.send.assert_awaited_once()
    
    kwargs = reportCh.send.call_args.kwargs
    embed = kwargs.get("embed")
    files = kwargs.get("files")
    
    assert embed is not None
    assert embed.image.url == "attachment://0_photo.png"
    assert files is not None
    assert len(files) == 2
    assert files[0].filename == "0_photo.png"
    assert files[1].filename == "1_voice.ogg"

@pytest.mark.asyncio
async def testSendEventReportSuccessMultipleEmbedsWithFiles(mockMessage, mockChannel, mockAttachment):
    service = ReportService()
    attImage1 = mockAttachment("photo1.png", "https://cdn.discordapp.com/photo1.png", data=b"img1")
    attImage2 = mockAttachment("photo2.png", "https://cdn.discordapp.com/photo2.png", data=b"img2")
    
    msg = mockMessage(content="multi media", attachments=[attImage1, attImage2])
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "detected", "log only")
    assert result is True
    reportCh.send.assert_awaited_once()
    
    kwargs = reportCh.send.call_args.kwargs
    embeds = kwargs.get("embeds")
    files = kwargs.get("files")
    
    assert embeds is not None
    assert len(embeds) == 2
    assert embeds[0].image.url == "attachment://0_photo1.png"
    assert embeds[1].image.url == "attachment://1_photo2.png"
    assert len(files) == 2

@pytest.mark.asyncio
async def testSendEventReportDiscordExceptionHandling(mockMessage, mockChannel):
    service = ReportService()
    msg = mockMessage()
    reportCh = mockChannel(channelId=33333, guild=msg.guild)
    reportCh.send.side_effect = discord.HTTPException(MagicMock(status=500), "Server Error")
    config = GuildConfig(guildId=99999, watchChannelId=11111, policy="enforced", reportChannelId=33333)
    
    result = await service.sendEventReport(config, msg, "detected", "log only")
    assert result is False

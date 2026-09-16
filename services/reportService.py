from dataclasses import dataclass
from datetime import datetime, timezone
import io
import logging
import discord
try:
    from discord.ui import LayoutView, Container, TextDisplay, Separator, MediaGallery
    hasComponentsV2 = True
except ImportError:
    hasComponentsV2 = False
    LayoutView = None
    Container = None
    TextDisplay = None
    Separator = None
    MediaGallery = None

from models.guildConfig import GuildConfig
from utils.logging import truncateContent

logger = logging.getLogger(__name__)

@dataclass
class SavedMedia:
    filename: str
    data: bytes
    isImage: bool

class ReportService:
    def __init__(self, maxContentLength: int = 500):
        self.maxContentLength = maxContentLength

    def isImageAttachment(self, attachment: discord.Attachment) -> bool:
        contentType = getattr(attachment, "content_type", None)
        if contentType and contentType.startswith("image/"):
            return True
        filename = getattr(attachment, "filename", "")
        imageExtensions = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")
        return filename.lower().endswith(imageExtensions)

    async def collectMedia(self, message: discord.Message) -> list[SavedMedia]:
        savedMediaList = []
        attachments = getattr(message, "attachments", [])
        for index, attachment in enumerate(attachments):
            try:
                data = await attachment.read()
                originalName = getattr(attachment, "filename", f"file_{index}")
                safeName = f"{index}_{originalName}"
                isImage = self.isImageAttachment(attachment)
                savedMediaList.append(SavedMedia(filename=safeName, data=data, isImage=isImage))
            except Exception as e:
                logger.warning(f"Failed to read attachment {getattr(attachment, 'id', index)}: {e}")

        stickers = getattr(message, "stickers", [])
        for index, sticker in enumerate(stickers):
            try:
                if hasattr(sticker, "read"):
                    data = await sticker.read()
                    savedMediaList.append(SavedMedia(filename=f"sticker_{index}.png", data=data, isImage=True))
            except Exception as e:
                logger.warning(f"Failed to read sticker {getattr(sticker, 'id', index)}: {e}")

        return savedMediaList

    def formatMessageContent(self, message: discord.Message, mediaList: list[SavedMedia] | None = None) -> str:
        boundedContent = truncateContent(getattr(message, "content", ""), self.maxContentLength)
        contentParts = []
        if boundedContent:
            contentParts.append(boundedContent)

        if mediaList:
            nonImageMedia = [m for m in mediaList if not m.isImage]
            if nonImageMedia:
                contentParts.append("\n".join(f"Attached file: {m.filename}" for m in nonImageMedia))

        if not contentParts:
            if mediaList:
                return ""
            return "<empty>"

        formatted = "\n\n".join(contentParts) if len(contentParts) > 1 else contentParts[0]
        if len(formatted) > 1024:
            return formatted[:1021] + "..."
        return formatted

    def createReportEmbed(
        self,
        guildConfig: GuildConfig,
        message: discord.Message,
        action: str,
        reason: str,
        mediaList: list[SavedMedia] | None = None
    ) -> discord.Embed:
        mediaItems = mediaList or []
        formattedContent = self.formatMessageContent(message, mediaItems)
        currentTimeStr = datetime.now(timezone.utc).strftime("%H:%M:%S %d/%m/%Y UTC")

        if action == "banned":
            statusDisplay = "Banned"
            color = discord.Color.red()
        elif action == "detected":
            statusDisplay = "Reported"
            color = discord.Color.blue()
        else:
            statusDisplay = f"Failed: {reason}"
            color = discord.Color.gold()

        embed = discord.Embed(title="BanInBlacklistedChannels Event Log", color=color)
        embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Status", value=statusDisplay, inline=False)
        embed.add_field(name="Message Content", value=formattedContent or "\u200b", inline=False)
        embed.set_footer(text=currentTimeStr)

        imageMedia = [m for m in mediaItems if m.isImage]
        if imageMedia:
            embed.set_image(url=f"attachment://{imageMedia[0].filename}")

        return embed

    def createReportLayoutView(
        self,
        guildConfig: GuildConfig,
        message: discord.Message,
        action: str,
        reason: str,
        mediaList: list[SavedMedia] | None = None
    ):
        if not hasComponentsV2:
            return self.createReportEmbed(guildConfig, message, action, reason, mediaList)

        mediaItems = mediaList or []
        formattedContent = self.formatMessageContent(message, mediaItems)
        currentTimeStr = datetime.now(timezone.utc).strftime("%H:%M:%S %d/%m/%Y UTC")

        if action == "banned":
            statusDisplay = "Banned"
            accentColor = discord.Color.red()
        elif action == "detected":
            statusDisplay = "Reported"
            accentColor = discord.Color.blue()
        else:
            statusDisplay = f"Failed: {reason}"
            accentColor = discord.Color.gold()

        view = LayoutView()
        container = Container(accent_color=accentColor)
        container.add_item(TextDisplay("## BanInBlacklistedChannels Event Log"))
        container.add_item(Separator())

        messageContentLine = f"**Message Content:** {formattedContent}" if formattedContent else "**Message Content:**"
        bodyText = (
            f"**User:** {message.author.mention} ({message.author.id})\n"
            f"**Status:** {statusDisplay}\n"
            f"{messageContentLine}"
        )
        container.add_item(TextDisplay(bodyText))

        imageMedia = [m for m in mediaItems if m.isImage]
        if imageMedia:
            galleryItems = [discord.MediaGalleryItem(f"attachment://{m.filename}") for m in imageMedia[:10]]
            gallery = MediaGallery(*galleryItems)
            container.add_item(gallery)

        container.add_item(Separator())
        container.add_item(TextDisplay(f"*{currentTimeStr}*"))
        view.add_item(container)
        return view

    async def sendEventReport(
        self,
        guildConfig: GuildConfig,
        message: discord.Message,
        action: str,
        reason: str,
        mediaList: list[SavedMedia] | None = None
    ) -> bool:
        if not guildConfig.reportChannelId:
            logger.info(f"No report channel configured for guild {message.guild.id}, skipping report.")
            return False

        reportChannel = message.guild.get_channel(guildConfig.reportChannelId)
        if reportChannel is None:
            logger.warning(f"Report channel {guildConfig.reportChannelId} not found in guild {message.guild.id}.")
            return False

        if mediaList is None:
            mediaList = await self.collectMedia(message)

        files = []
        for m in mediaList:
            buf = io.BytesIO(m.data)
            buf.seek(0)
            files.append(discord.File(fp=buf, filename=m.filename))

        try:
            if hasComponentsV2:
                view = self.createReportLayoutView(guildConfig, message, action, reason, mediaList)
                if files:
                    await reportChannel.send(view=view, files=files)
                else:
                    await reportChannel.send(view=view)
            else:
                embed = self.createReportEmbed(guildConfig, message, action, reason, mediaList)
                if files:
                    await reportChannel.send(embed=embed, files=files)
                else:
                    await reportChannel.send(embed=embed)
            return True
        except discord.DiscordException as e:
            logger.warning(f"Discord exception sending report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to send report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False

from datetime import datetime, timezone
import logging
import discord
from models.guildConfig import GuildConfig
from utils.logging import truncateContent

logger = logging.getLogger(__name__)

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

    def formatMessageContent(self, message: discord.Message) -> str:
        boundedContent = truncateContent(getattr(message, "content", ""), self.maxContentLength)
        contentParts = []
        if boundedContent:
            contentParts.append(boundedContent)

        mediaParts = []
        attachments = getattr(message, "attachments", [])
        if attachments:
            for attachment in attachments:
                url = getattr(attachment, "url", None)
                filename = getattr(attachment, "filename", "attachment")
                if url and not self.isImageAttachment(attachment):
                    mediaParts.append(f"[{filename}]({url})")

        if mediaParts:
            contentParts.append("\n".join(mediaParts))

        if not contentParts:
            return "<empty>"

        formatted = "\n\n".join(contentParts) if len(contentParts) > 1 else contentParts[0]
        if len(formatted) > 1024:
            return formatted[:1021] + "..."
        return formatted

    def createReportEmbeds(
        self,
        guildConfig: GuildConfig,
        message: discord.Message,
        action: str,
        reason: str
    ) -> list[discord.Embed]:
        formattedContent = self.formatMessageContent(message)
        currentTimeStr = datetime.now(timezone.utc).strftime("%H:%M:%S %d/%m/%Y UTC")

        if action == "banned":
            statusDisplay = "Banned"
        elif action == "detected":
            statusDisplay = "Reported"
        else:
            statusDisplay = f"Failed: {reason}"

        imageUrls = []
        attachments = getattr(message, "attachments", [])
        if attachments:
            for attachment in attachments:
                url = getattr(attachment, "url", None)
                if url and self.isImageAttachment(attachment):
                    imageUrls.append(url)

        stickers = getattr(message, "stickers", [])
        if stickers:
            for sticker in stickers:
                url = getattr(sticker, "url", None)
                if url:
                    imageUrls.append(url)

        mainEmbed = discord.Embed(title="BanInBlacklistedChannels Event Log")
        mainEmbed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
        mainEmbed.add_field(name="Status", value=statusDisplay, inline=False)
        mainEmbed.add_field(name="Message Content", value=formattedContent, inline=False)
        mainEmbed.set_footer(text=currentTimeStr)

        if imageUrls:
            mainEmbed.set_image(url=imageUrls[0])

        embeds = [mainEmbed]
        for url in imageUrls[1:10]:
            subEmbed = discord.Embed()
            subEmbed.set_image(url=url)
            embeds.append(subEmbed)

        return embeds

    async def sendEventReport(
        self,
        guildConfig: GuildConfig,
        message: discord.Message,
        action: str,
        reason: str
    ) -> bool:
        if not guildConfig.reportChannelId:
            logger.info(f"No report channel configured for guild {message.guild.id}, skipping report.")
            return False

        reportChannel = message.guild.get_channel(guildConfig.reportChannelId)
        if reportChannel is None:
            logger.warning(f"Report channel {guildConfig.reportChannelId} not found in guild {message.guild.id}.")
            return False

        embeds = self.createReportEmbeds(guildConfig, message, action, reason)

        try:
            if len(embeds) == 1:
                await reportChannel.send(embed=embeds[0])
            else:
                await reportChannel.send(embeds=embeds)
            return True
        except discord.DiscordException as e:
            logger.warning(f"Discord exception sending report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to send report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False

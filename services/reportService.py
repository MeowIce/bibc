from datetime import datetime, timezone
import logging
import discord
from models.guildConfig import GuildConfig
from utils.logging import truncateContent

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, maxContentLength: int = 500):
        self.maxContentLength = maxContentLength

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
                if url:
                    mediaParts.append(f"[{filename}]({url})")

        stickers = getattr(message, "stickers", [])
        if stickers:
            for sticker in stickers:
                url = getattr(sticker, "url", None)
                name = getattr(sticker, "name", "sticker")
                if url:
                    mediaParts.append(f"[{name}]({url})")

        if mediaParts:
            contentParts.append("\n".join(mediaParts))

        if not contentParts:
            return "<empty>"

        formatted = "\n\n".join(contentParts) if len(contentParts) > 1 else contentParts[0]
        if len(formatted) > 1024:
            return formatted[:1021] + "..."
        return formatted

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

        formattedContent = self.formatMessageContent(message)
        currentTimeStr = datetime.now(timezone.utc).strftime("%H:%M:%S %d/%m/%Y UTC")

        if action == "banned":
            statusDisplay = "Banned"
        elif action == "detected":
            statusDisplay = "Reported"
        else:
            statusDisplay = f"Failed: {reason}"

        embed = discord.Embed(title="BanInBlacklistedChannels Event Log")
        embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Status", value=statusDisplay, inline=False)
        embed.add_field(name="Message Content", value=formattedContent, inline=False)
        embed.set_footer(text=currentTimeStr)

        try:
            await reportChannel.send(embed=embed)
            return True
        except discord.DiscordException as e:
            logger.warning(f"Discord exception sending report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to send report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False

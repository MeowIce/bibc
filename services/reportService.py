import logging
from datetime import datetime, timezone
import discord
from models.guildConfig import GuildConfig

logger = logging.getLogger(__name__)

class ReportService:
    def __init__(self, maxContentLength: int = 500):
        self.maxContentLength = maxContentLength

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

        boundedContent = message.content[:self.maxContentLength]
        if len(message.content) > self.maxContentLength:
            boundedContent += "..."

        currentTimeStr = datetime.now(timezone.utc).strftime("%H:%M:%S %d/%m/%Y UTC")

        embed = discord.Embed(title="BanInBlacklistedChannels Event Log")
        embed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
        embed.add_field(name="Status", value=action, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Content", value=boundedContent if boundedContent else "<empty>", inline=False)
        embed.set_footer(text=currentTimeStr)

        try:
            await reportChannel.send(embed=embed)
            return True
        except Exception as e:
            logger.warning(f"Failed to send report to channel {guildConfig.reportChannelId} in guild {message.guild.id}: {e}")
            return False

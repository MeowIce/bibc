from collections import OrderedDict
from datetime import datetime, timezone
import logging
import discord
from services.guildConfigService import GuildConfigService
from services.banService import BanService, BanResult
from services.reportService import ReportService

logger = logging.getLogger(__name__)

class MessageWatcher:
    def __init__(
        self,
        bot,
        guildConfigService: GuildConfigService,
        banService: BanService,
        reportService: ReportService,
        maxCacheSize: int = 1000
    ):
        self.bot = bot
        self.guildConfigService = guildConfigService
        self.banService = banService
        self.reportService = reportService
        self.maxCacheSize = maxCacheSize
        self._processedEvents = OrderedDict()

    def _isDuplicate(self, guildId: int, messageId: int) -> bool:
        key = (guildId, messageId)
        if key in self._processedEvents:
            return True
        self._processedEvents[key] = True
        if len(self._processedEvents) > self.maxCacheSize:
            self._processedEvents.popitem(last=False)
        return False

    async def handleMessage(self, message: discord.Message) -> bool:
        try:
            botUser = getattr(self.bot, "user", None)
            if botUser and message.author.id == botUser.id:
                return False

            if getattr(message.author, "bot", False):
                return False

            if message.guild is None:
                return False

            if self._isDuplicate(message.guild.id, message.id):
                return False

            guildConfig = self.guildConfigService.getConfig(message.guild.id)
            if guildConfig is None or guildConfig.watchChannelId is None:
                return False

            if message.channel.id != guildConfig.watchChannelId:
                return False

            botStartTime = getattr(self.bot, "startTime", None)
            messageCreatedAt = getattr(message, "created_at", None)
            if isinstance(botStartTime, datetime) and isinstance(messageCreatedAt, datetime):
                if messageCreatedAt.tzinfo is None:
                    messageCreatedAt = messageCreatedAt.replace(tzinfo=timezone.utc)
                if botStartTime.tzinfo is None:
                    botStartTime = botStartTime.replace(tzinfo=timezone.utc)
                if messageCreatedAt < botStartTime:
                    return False

            mediaList = await self.reportService.collectMedia(message)
            try:
                await message.delete()
            except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
                logger.warning(f"Failed to delete message {message.id} in channel {message.channel.id}: {e}")
            except Exception as e:
                logger.warning(f"Unexpected error deleting message {message.id}: {e}")

            banResult = await self.banService.handleMessage(message, guildConfig)
            await self.reportService.sendEventReport(
                guildConfig=guildConfig,
                message=message,
                action=banResult.action,
                reason=banResult.reason,
                mediaList=mediaList
            )
            return True
        except Exception as e:
            logger.exception(f"Unexpected error handling message {getattr(message, 'id', None)}: {e}")
            return False

async def handleMessageEvent(message: discord.Message, watchedChannelId: int, policy: str, startTime: datetime | None = None) -> bool:
    if message.author.bot or message.guild is None:
        return False
    if message.channel.id != watchedChannelId:
        return False
    messageCreatedAt = getattr(message, "created_at", None)
    if isinstance(startTime, datetime) and isinstance(messageCreatedAt, datetime):
        if messageCreatedAt.tzinfo is None:
            messageCreatedAt = messageCreatedAt.replace(tzinfo=timezone.utc)
        if startTime.tzinfo is None:
            startTime = startTime.replace(tzinfo=timezone.utc)
        if messageCreatedAt < startTime:
            return False
    try:
        await message.delete()
    except Exception:
        pass
    if policy == "enforced":
        await message.guild.ban(
            message.author,
            reason="gửi tin nhắn vào kênh lọc spam",
            delete_message_seconds=300
        )
    return True

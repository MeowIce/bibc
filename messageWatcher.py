from collections import OrderedDict
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

        banResult = await self.banService.handleMessage(message, guildConfig)
        await self.reportService.sendEventReport(
            guildConfig=guildConfig,
            message=message,
            action=banResult.action,
            reason=banResult.reason
        )
        return True

async def handleMessageEvent(message: discord.Message, watchedChannelId: int, policy: str) -> bool:
    if message.author.bot or message.guild is None:
        return False
    if message.channel.id != watchedChannelId:
        return False
    if policy == "enforced":
        await message.guild.ban(
            message.author,
            reason="gửi tin nhắn vào kênh lọc spam",
            delete_message_seconds=300
        )
    return True

from unittest.mock import AsyncMock, MagicMock
import pytest
from database import Database
from repositories.guildConfigRepository import GuildConfigRepository
from repositories.banRepository import BanRepository
from services.guildConfigService import GuildConfigService
from services.banService import BanService
from services.reportService import ReportService

try:
    from messageWatcher import MessageWatcher, handleMessageEvent
except ImportError:
    MessageWatcher = None
    handleMessageEvent = None

@pytest.fixture
def watcherSetup(tmp_path):
    db = Database(str(tmp_path / "watcher.db"))
    db.initialize()
    guildRepo = GuildConfigRepository(db)
    configService = GuildConfigService(guildRepo)
    banRepo = BanRepository(db)
    banService = BanService(banRepo)
    reportService = ReportService()
    bot = MagicMock()
    bot.user.id = 999999
    bot.process_commands = AsyncMock()
    watcher = MessageWatcher(bot=bot, guildConfigService=configService, banService=banService, reportService=reportService)
    return watcher, configService, banService, banRepo, db

@pytest.mark.asyncio
async def testWatchedChannelDetection(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    guildId = 99999
    watchedChannelId = 11111
    unrelatedChannelId = 22222
    
    configService.setWatchChannel(guildId, watchedChannelId)
    configService.setPolicy(guildId, "enforced")
    
    watchedMsg = mockMessage(channelId=watchedChannelId, guildId=guildId)
    unrelatedMsg = mockMessage(channelId=unrelatedChannelId, guildId=guildId)
    
    handled = await watcher.handleMessage(watchedMsg)
    ignored = await watcher.handleMessage(unrelatedMsg)
    
    assert handled is True
    assert ignored is False
    db.close()

@pytest.mark.asyncio
async def testEnforcedPolicyBan(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    guildId = 99999
    channelId = 11111
    configService.setWatchChannel(guildId, channelId)
    configService.setPolicy(guildId, "enforced")
    
    msg = mockMessage(channelId=channelId, guildId=guildId)
    await watcher.handleMessage(msg)
    
    msg.guild.ban.assert_awaited_once_with(
        msg.author,
        reason="gửi tin nhắn vào kênh lọc spam",
        delete_message_seconds=300
    )
    db.close()

@pytest.mark.asyncio
async def testPermissivePolicyNoBan(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    guildId = 99999
    channelId = 11111
    configService.setWatchChannel(guildId, channelId)
    configService.setPolicy(guildId, "permissive")
    
    msg = mockMessage(channelId=channelId, guildId=guildId)
    await watcher.handleMessage(msg)
    
    msg.guild.ban.assert_not_awaited()
    db.close()

@pytest.mark.asyncio
async def testBotAuthorExcluded(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    guildId = 99999
    channelId = 11111
    configService.setWatchChannel(guildId, channelId)
    configService.setPolicy(guildId, "enforced")
    
    msg = mockMessage(channelId=channelId, guildId=guildId, isBot=True)
    handled = await watcher.handleMessage(msg)
    
    assert handled is False
    msg.guild.ban.assert_not_awaited()
    db.close()

@pytest.mark.asyncio
async def testDmExcluded(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    msg = mockMessage(isDm=True)
    handled = await watcher.handleMessage(msg)
    
    assert handled is False
    db.close()

@pytest.mark.asyncio
async def testUnconfiguredGuildIgnored(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    msg = mockMessage(guildId=88888)
    handled = await watcher.handleMessage(msg)
    
    assert handled is False
    msg.guild.ban.assert_not_awaited()
    db.close()

@pytest.mark.asyncio
async def testDuplicateRapidMessages(mockMessage, watcherSetup):
    watcher, configService, banService, banRepo, db = watcherSetup
    guildId = 99999
    channelId = 11111
    configService.setWatchChannel(guildId, channelId)
    configService.setPolicy(guildId, "enforced")
    
    msg = mockMessage(channelId=channelId, guildId=guildId)
    firstResult = await watcher.handleMessage(msg)
    secondResult = await watcher.handleMessage(msg)
    
    assert firstResult is True
    assert secondResult is False
    assert msg.guild.ban.await_count == 1
    db.close()

from unittest.mock import AsyncMock, MagicMock
import discord
import pytest
from database import Database
from repositories.guildConfigRepository import GuildConfigRepository
from repositories.banRepository import BanRepository
from services.guildConfigService import GuildConfigService
from services.banService import BanService
from services.reportService import ReportService
from services.statisticsService import StatisticsService
from messageWatcher import MessageWatcher

@pytest.fixture
def integrationPipeline(tmp_path):
    dbPath = str(tmp_path / "integration.db")
    db = Database(dbPath)
    db.initialize()
    
    guildRepo = GuildConfigRepository(db)
    guildService = GuildConfigService(guildRepo)
    
    banRepo = BanRepository(db)
    banService = BanService(banRepo)
    
    reportService = ReportService()
    statService = StatisticsService(banRepo)
    
    bot = MagicMock()
    bot.user.id = 999999
    bot.process_commands = AsyncMock()
    
    watcher = MessageWatcher(
        bot=bot,
        guildConfigService=guildService,
        banService=banService,
        reportService=reportService
    )
    
    return {
        "dbPath": dbPath,
        "db": db,
        "guildService": guildService,
        "banRepo": banRepo,
        "statService": statService,
        "reportService": reportService,
        "watcher": watcher
    }

@pytest.mark.asyncio
async def testEnforcedIntegrationPipeline(mockMessage, mockChannel, integrationPipeline):
    guildId = 10001
    watchChId = 20001
    reportChId = 30001
    
    p = integrationPipeline
    p["guildService"].setWatchChannel(guildId, watchChId)
    p["guildService"].setPolicy(guildId, "enforced")
    p["guildService"].setReportChannel(guildId, reportChId)
    
    msg = mockMessage(channelId=watchChId, guildId=guildId, authorId=70001)
    reportCh = mockChannel(channelId=reportChId, guild=msg.guild)
    
    handled = await p["watcher"].handleMessage(msg)
    assert handled is True
    
    msg.guild.ban.assert_awaited_once_with(
        msg.author,
        reason="gửi tin nhắn vào kênh lọc spam",
        delete_message_seconds=300
    )
    
    assert p["statService"].countTotal(guildId) == 1
    reportCh.send.assert_awaited_once()
    
    embed = reportCh.send.call_args.kwargs.get("embed")
    assert embed is not None
    fieldDict = {f.name: f.value for f in embed.fields}
    assert "User" in fieldDict
    assert "Status" in fieldDict
    assert fieldDict["Status"] == "Banned"
    assert "Message Content" in fieldDict
    
    p["db"].close()

@pytest.mark.asyncio
async def testPermissiveIntegrationPipeline(mockMessage, mockChannel, integrationPipeline):
    guildId = 10002
    watchChId = 20002
    reportChId = 30002
    
    p = integrationPipeline
    p["guildService"].setWatchChannel(guildId, watchChId)
    p["guildService"].setPolicy(guildId, "permissive")
    p["guildService"].setReportChannel(guildId, reportChId)
    
    msg = mockMessage(channelId=watchChId, guildId=guildId, authorId=70002)
    reportCh = mockChannel(channelId=reportChId, guild=msg.guild)
    
    handled = await p["watcher"].handleMessage(msg)
    assert handled is True
    
    msg.guild.ban.assert_not_awaited()
    assert p["statService"].countTotal(guildId) == 0
    reportCh.send.assert_awaited_once()
    
    embed = reportCh.send.call_args.kwargs.get("embed")
    assert embed is not None
    fieldDict = {f.name: f.value for f in embed.fields}
    assert fieldDict["Status"] == "Reported"
    
    p["db"].close()

@pytest.mark.asyncio
async def testRestartPersistence(mockMessage, integrationPipeline):
    guildId = 10003
    watchChId = 20003
    
    p = integrationPipeline
    p["guildService"].setWatchChannel(guildId, watchChId)
    p["guildService"].setPolicy(guildId, "enforced")
    
    msg = mockMessage(channelId=watchChId, guildId=guildId, authorId=70003)
    await p["watcher"].handleMessage(msg)
    
    p["db"].close()
    
    reopenedDb = Database(p["dbPath"])
    reopenedGuildRepo = GuildConfigRepository(reopenedDb)
    reopenedBanRepo = BanRepository(reopenedDb)
    reopenedStatService = StatisticsService(reopenedBanRepo)
    
    loadedConfig = reopenedGuildRepo.get(guildId)
    assert loadedConfig is not None
    assert loadedConfig.watchChannelId == watchChId
    assert loadedConfig.policy == "enforced"
    assert reopenedStatService.countTotal(guildId) == 1
    
    reopenedDb.close()

@pytest.mark.asyncio
async def testMissingConfigIntegration(mockMessage, integrationPipeline):
    p = integrationPipeline
    msg = mockMessage(channelId=99999, guildId=88888, authorId=77777)
    
    handled = await p["watcher"].handleMessage(msg)
    assert handled is False
    msg.guild.ban.assert_not_awaited()
    assert p["statService"].countTotal(88888) == 0
    
    p["db"].close()

@pytest.mark.asyncio
async def testPermissionFailureIntegration(mockMessage, integrationPipeline):
    guildId = 10004
    watchChId = 20004
    
    p = integrationPipeline
    p["guildService"].setWatchChannel(guildId, watchChId)
    p["guildService"].setPolicy(guildId, "enforced")
    
    msg = mockMessage(channelId=watchChId, guildId=guildId, authorId=70004)
    response = MagicMock()
    response.status = 403
    response.reason = "Forbidden"
    msg.guild.ban.side_effect = discord.Forbidden(response, "Missing Permissions")
    
    handled = await p["watcher"].handleMessage(msg)
    assert handled is True
    assert p["statService"].countTotal(guildId) == 0
    
    recentRecords = p["banRepo"].getRecent(guildId)
    assert len(recentRecords) == 1
    assert recentRecords[0].action == "failed"
    
    p["db"].close()

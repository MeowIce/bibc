from datetime import datetime, timezone
import logging
import discord
from discord.ext import commands

from config import loadConfig, AppConfig
from database import Database
from repositories.guildConfigRepository import GuildConfigRepository
from repositories.banRepository import BanRepository
from services.guildConfigService import GuildConfigService
from services.banService import BanService
from services.reportService import ReportService
from services.statisticsService import StatisticsService
from messageWatcher import MessageWatcher
from cogs.config import ConfigCog
from cogs.status import StatusCog, updateBotStatus
from utils.logging import configureLogging

logger = logging.getLogger("bibc")

class BibcBot(commands.Bot):
    def __init__(self, config: AppConfig):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix="!", intents=intents)

        self.config = config
        self.startTime = datetime.now(timezone.utc)
        self.database = Database(config.databasePath)
        self.guildConfigRepo = GuildConfigRepository(self.database)
        self.guildConfigService = GuildConfigService(self.guildConfigRepo)
        self.banRepo = BanRepository(self.database)
        self.banService = BanService(self.banRepo)
        self.reportService = ReportService()
        self.statisticsService = StatisticsService(self.banRepo)
        self.messageWatcher = MessageWatcher(
            self,
            self.guildConfigService,
            self.banService,
            self.reportService
        )

    async def setup_hook(self):
        self.database.initialize()
        await self.add_cog(ConfigCog(self.guildConfigService))
        await self.add_cog(
            StatusCog(
                self,
                self.statisticsService,
                self.guildConfigService,
                self.startTime
            )
        )
        await self.tree.sync()
        logger.info("Application setup complete, database initialized, and command tree synced.")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id}).")
        logger.info(f"Monitoring total guilds: {len(self.guilds)}.")
        await updateBotStatus(self)

    async def on_message(self, message: discord.Message):
        await self.messageWatcher.handleMessage(message)
        await self.process_commands(message)

    async def close(self):
        try:
            self.database.close()
            logger.info("Database connection closed cleanly.")
        except Exception as e:
            logger.exception(f"Error closing database: {e}")
        finally:
            await super().close()

def main():
    configureLogging()
    logger.info("Starting BIBC v2.0...")
    config = loadConfig()
    bot = BibcBot(config)
    try:
        bot.run(config.discordToken, log_handler=None)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Process terminated by signal.")

if __name__ == "__main__":
    main()
from datetime import datetime, timezone
import logging
import discord
from discord import app_commands
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
        self.banService = BanService(self.banRepo, startTime=self.startTime)
        self.reportService = ReportService()
        self.statisticsService = StatisticsService(self.banRepo)
        self.messageWatcher = MessageWatcher(
            self,
            self.guildConfigService,
            self.banService,
            self.reportService
        )
        self._setupTreeErrorHandler()

    def _setupTreeErrorHandler(self):
        async def onTreeError(interaction: discord.Interaction, error: app_commands.AppCommandError):
            if isinstance(error, app_commands.CommandNotFound):
                commandName = getattr(error, "name", "unknown")
                logger.warning(f"Ignored outdated application command '{commandName}' from user {interaction.user.id}")
                if not interaction.response.is_done():
                    await interaction.response.send_message("Lệnh này không còn tồn tại hoặc đã lỗi thời.", ephemeral=True)
                return
            logger.exception(f"Unhandled error in command tree: {error}")

        self.tree.on_error = onTreeError

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
        logger.info("Application setup complete, database initialized, and global command tree synced.")

    async def on_ready(self):
        await updateBotStatus(self)
        for guild in self.guilds:
            try:
                self.tree.clear_commands(guild=guild)
                await self.tree.sync(guild=guild)
            except Exception as e:
                logger.warning(f"Failed to clear old guild commands for guild {guild.id}: {e}")

        divider = "=" * 60
        readyBanner = (
            f"\n{divider}\n"
            f"  BIBC BOT ONLINE & OPERATIONAL\n"
            f"  Bot User  : {self.user} (ID: {self.user.id})\n"
            f"  Guilds    : {len(self.guilds)} connected\n"
            f"  Database  : {self.config.databasePath}\n"
            f"  Watcher   : Honeypot monitoring active\n"
            f"{divider}"
        )
        logger.info(readyBanner)

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
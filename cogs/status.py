from datetime import datetime, timezone
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import LayoutView, Container, TextDisplay, Separator
from services.statisticsService import StatisticsService
from services.guildConfigService import GuildConfigService

def formatActivityString(serverCount: int, memberCount: int) -> str:
    return f"Status type: watching, {serverCount} servers - {memberCount} members"

def calculateMemberCount(guilds) -> int:
    total = 0
    for guild in guilds:
        total += getattr(guild, "member_count", 0) or 0
    return total

async def updateBotStatus(bot):
    serverCount = len(bot.guilds)
    memberCount = calculateMemberCount(bot.guilds)
    statusText = formatActivityString(serverCount, memberCount)
    activity = discord.CustomActivity(name=statusText)
    await bot.change_presence(activity=activity)

class StatusCog(commands.Cog):
    def __init__(
        self,
        bot,
        statisticsService: StatisticsService,
        guildConfigService: GuildConfigService,
        startTime: datetime | None = None,
        developerId: str = "<@666824403216105483>",
        supportServerUrl: str = "https://dsc.gg/meowsmp"
    ):
        self.bot = bot
        self.statisticsService = statisticsService
        self.guildConfigService = guildConfigService
        self.startTime = startTime if startTime is not None else datetime.now(timezone.utc)
        self.developerId = developerId
        self.supportServerUrl = supportServerUrl

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await updateBotStatus(self.bot)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await updateBotStatus(self.bot)

    @app_commands.command(name="status", description="About BIBC...")
    async def status(self, interaction: discord.Interaction):
        currentDuration = datetime.now(timezone.utc) - self.startTime
        totalSeconds = int(currentDuration.total_seconds())
        hours, remainder = divmod(totalSeconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        currentPolicy = "N/A (DMs)"
        if interaction.guild_id is not None:
            cfg = self.guildConfigService.getConfig(interaction.guild_id)
            if cfg is not None:
                currentPolicy = f"`{cfg.policy}`"

        totalBans = self.statisticsService.countTotal(interaction.guild_id)
        monthBans = self.statisticsService.countThisMonth(interaction.guild_id)
        weekBans = self.statisticsService.countThisWeek(interaction.guild_id)

        botUserId = getattr(self.bot.user, "id", "Unknown")

        view = LayoutView()
        container = Container(accent_color=discord.Color.blurple())
        container.add_item(TextDisplay("## About BanInBlacklistedChannels Bot..."))
        container.add_item(Separator())

        details = (
            f"**Developer:** {self.developerId}\n"
            f"**Bot ID:** `{botUserId}`\n"
            f"**Execution Policy:** {currentPolicy}\n"
            f"**Uptime:** {days}d {hours}h {minutes}m {seconds}s\n"
            f"**Support Server:** {self.supportServerUrl}\n"
            f"**Banned (Total / Month / Week):** {totalBans} / {monthBans} / {weekBans}"
        )
        container.add_item(TextDisplay(details))
        container.add_item(Separator())

        footerText = (
            "*Want me to protect your server ?*\n"
            "*Join the Support Server or DM the Dev to get started !*"
        )
        container.add_item(TextDisplay(footerText))
        view.add_item(container)

        await interaction.response.send_message(view=view)

async def setup(bot):
    statisticsService = getattr(bot, "statisticsService", None)
    guildConfigService = getattr(bot, "guildConfigService", None)
    startTime = getattr(bot, "startTime", None)
    if statisticsService and guildConfigService:
        await bot.add_cog(StatusCog(bot, statisticsService, guildConfigService, startTime))

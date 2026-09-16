from datetime import datetime, timezone
import logging
import discord
from discord import app_commands
from discord.ext import commands, tasks
try:
    from discord.ui import LayoutView, Container, TextDisplay, Separator, ActionRow, Button
    hasComponentsV2 = True
except ImportError:
    hasComponentsV2 = False
    LayoutView = None
    Container = None
    TextDisplay = None
    Separator = None
    ActionRow = None
    Button = None

from services.statisticsService import StatisticsService
from services.guildConfigService import GuildConfigService

logger = logging.getLogger(__name__)

def formatActivityString(serverCount: int, memberCount: int, bannedCount: int = 0) -> str:
    return f"{serverCount} servers, {memberCount} members, banned {bannedCount} accounts"

def calculateMemberCount(guilds) -> int:
    total = 0
    for guild in guilds:
        count = getattr(guild, "member_count", None)
        if count is None or count == 0:
            count = len(getattr(guild, "members", []))
        total += count or 0
    return total

async def updateBotStatus(bot):
    try:
        guilds = list(getattr(bot, "guilds", []))
    except Exception:
        guilds = []
    serverCount = len(guilds)
    memberCount = calculateMemberCount(guilds)
    statisticsService = getattr(bot, "statisticsService", None)
    bannedCount = 0
    if statisticsService and hasattr(statisticsService, "countTotal"):
        try:
            bannedCount = statisticsService.countTotal()
        except Exception:
            bannedCount = 0
    statusText = formatActivityString(serverCount, memberCount, bannedCount)
    activity = discord.Activity(type=discord.ActivityType.watching, name=statusText)
    if hasattr(bot, "change_presence"):
        try:
            await bot.change_presence(activity=activity)
            logger.info(f"Bot presence updated: Watching {statusText}")
        except Exception as e:
            logger.warning(f"Failed to change bot presence: {e}")

def getMinimalBotInviteUrl(botUserId: int) -> str:
    permissions = discord.Permissions(
        ban_members=True,
        manage_messages=True,
        view_channel=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        read_message_history=True
    )
    return discord.utils.oauth_url(
        botUserId,
        permissions=permissions,
        scopes=("bot", "applications.commands")
    )

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

    async def cog_load(self):
        self.statusUpdateLoop.start()

    async def cog_unload(self):
        self.statusUpdateLoop.cancel()

    @tasks.loop(minutes=5)
    async def statusUpdateLoop(self):
        await updateBotStatus(self.bot)

    @statusUpdateLoop.before_loop
    async def beforeStatusUpdateLoop(self):
        if hasattr(self.bot, "wait_until_ready"):
            await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        await updateBotStatus(self.bot)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        await updateBotStatus(self.bot)

    @commands.Cog.listener()
    async def on_guild_available(self, guild):
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

        if hasComponentsV2:
            view = LayoutView()
            container = Container()
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
                "Want me to protect your server ?\n"
                "Use the `/invite` command to get started !"
            )
            container.add_item(TextDisplay(footerText))
            view.add_item(container)
            await interaction.response.send_message(view=view)
        else:
            infoEmbed = discord.Embed(title="About BanInBlacklistedChannels Bot...")
            infoEmbed.add_field(name="Developer", value=self.developerId, inline=False)
            infoEmbed.add_field(name="Bot ID", value=f"`{botUserId}`", inline=False)
            infoEmbed.add_field(name="Execution Policy", value=currentPolicy, inline=False)
            infoEmbed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=False)
            infoEmbed.add_field(name="Support Server", value=self.supportServerUrl, inline=False)
            infoEmbed.add_field(name="Banned (Total / Month / Week)", value=f"{totalBans} / {monthBans} / {weekBans}", inline=False)
            infoEmbed.set_footer(text="Want me to protect your server ?\nUse the `/invite` command to get started !")
            await interaction.response.send_message(embed=infoEmbed)

    @app_commands.command(name="about", description="About BanInBlacklistedChannels Bot...")
    async def about(self, interaction: discord.Interaction):
        await self.status.callback(self, interaction)

    @app_commands.command(name="invite", description="Get the invite link to add BIBC to your server...")
    async def invite(self, interaction: discord.Interaction):
        botUserId = getattr(getattr(self.bot, "user", None), "id", None) or getattr(getattr(interaction, "client", None), "user", None).id
        inviteUrl = getMinimalBotInviteUrl(botUserId)

        if hasComponentsV2:
            view = LayoutView()
            container = Container()
            container.add_item(TextDisplay("## Invite BanInBlacklistedChannels Bot"))
            container.add_item(Separator())
            container.add_item(TextDisplay("Protect your server against spam and automated raids by inviting BIBC into your channels."))
            actionRow = ActionRow(Button(label="Invite Bot", style=discord.ButtonStyle.link, url=inviteUrl))
            container.add_item(actionRow)
            container.add_item(Separator())
            container.add_item(TextDisplay("*Note: Ensure the bot's role is placed above regular members.*"))
            view.add_item(container)
            await interaction.response.send_message(view=view)
        else:
            inviteEmbed = discord.Embed(
                title="Invite BanInBlacklistedChannels Bot",
                description="Protect your server against spam and automated raids by inviting BIBC into your channels."
            )
            inviteEmbed.set_footer(text="Note: Ensure the bot's role is placed above regular members.")
            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="Invite Bot", style=discord.ButtonStyle.link, url=inviteUrl))
            await interaction.response.send_message(embed=inviteEmbed, view=view)

async def setup(bot):
    statisticsService = getattr(bot, "statisticsService", None)
    guildConfigService = getattr(bot, "guildConfigService", None)
    startTime = getattr(bot, "startTime", None)
    if statisticsService and guildConfigService:
        await bot.add_cog(StatusCog(bot, statisticsService, guildConfigService, startTime))

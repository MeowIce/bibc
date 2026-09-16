import discord
from discord import app_commands
from discord.ext import commands
from services.guildConfigService import GuildConfigService
from models.guildConfig import ALLOWED_POLICIES

class ConfigCog(commands.GroupCog, name="config"):
    def __init__(self, guildConfigService: GuildConfigService):
        self.guildConfigService = guildConfigService
        super().__init__()

    @app_commands.command(name="watchchannel", description="Set the honeypot watch channel for this server.")
    @app_commands.default_permissions(administrator=True)
    async def watchchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or interaction.guild_id is None:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        if not getattr(interaction.user.guild_permissions, "administrator", False):
            await interaction.response.send_message("Requires Administrator permission.", ephemeral=True)
            return

        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Channel does not belong to current server.", ephemeral=True)
            return

        self.guildConfigService.setWatchChannel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Watch channel set to {channel.mention} (`{channel.id}`)")

    @app_commands.command(name="reportchannel", description="Set the event report channel for this server.")
    @app_commands.default_permissions(administrator=True)
    async def reportchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        if interaction.guild is None or interaction.guild_id is None:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        if not getattr(interaction.user.guild_permissions, "administrator", False):
            await interaction.response.send_message("Requires Administrator permission.", ephemeral=True)
            return

        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Channel does not belong to current server.", ephemeral=True)
            return

        self.guildConfigService.setReportChannel(interaction.guild_id, channel.id)
        await interaction.response.send_message(f"Report channel set to {channel.mention} (`{channel.id}`)")

    @app_commands.command(name="policy", description="Set moderation policy for this server.")
    @app_commands.choices(policy=[
        app_commands.Choice(name="enforced", value="enforced"),
        app_commands.Choice(name="permissive", value="permissive")
    ])
    @app_commands.default_permissions(administrator=True)
    async def policy(self, interaction: discord.Interaction, policy: str):
        if interaction.guild is None or interaction.guild_id is None:
            await interaction.response.send_message("Server only.", ephemeral=True)
            return

        if not getattr(interaction.user.guild_permissions, "administrator", False):
            await interaction.response.send_message("Requires Administrator permission.", ephemeral=True)
            return

        if policy not in ALLOWED_POLICIES:
            await interaction.response.send_message(f"Invalid policy. Choose one of: {', '.join(ALLOWED_POLICIES)}", ephemeral=True)
            return

        self.guildConfigService.setPolicy(interaction.guild_id, policy)
        await interaction.response.send_message(f"Execution policy set to `{policy}`")

async def setup(bot):
    guildConfigService = getattr(bot, "guildConfigService", None)
    if guildConfigService is not None:
        await bot.add_cog(ConfigCog(guildConfigService))

# Copyright (c) 2026 MeowIce

# Permission is granted to use, modify, and distribute this software for non-commercial purposes only.
# Selling this software or any derivative works is prohibited without explicit written permission.
# Removing or altering author credits is prohibited.

import discord
from discord.ext import commands
from discord import app_commands
import datetime

# ==== CONFIG ====
botToken = ""
ChID = [123456789, 987654321]
reportChID = [12345654321, 65432123456]
actionReason = "gửi tin nhắn vào kênh lọc spam"
isLogOnlyMode = 0
# =================

PolicyModes = {}
bannedUsers = []
startTime = datetime.datetime.now(datetime.timezone.utc)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print("This is BanInBlacklistedChannels (BIBC), developed by MeowIce. Version 2.0")
    print("Source code: https://github.com/MeowIce/bibc")
    print(f"Logged in as {bot.user} (ID: {bot.user.id}).")
    print("Monitoring total channels: " + str(len(bot.guilds)) + " | " + "Monitoring total users: " + str(len(bot.users)))
    print(f"The current Execution Policy is set to: {'LogOnly' if isLogOnlyMode else 'Enforced'}")
    print("------")
    for guild in bot.guilds:
        PolicyModes[guild.id] = isLogOnlyMode

@bot.tree.command(name="epedit", description="Change execution policy.")
@app_commands.default_permissions(administrator=True)
async def toggleLogOnly(interaction: discord.Interaction):
    guildId = interaction.guild_id
    if guildId is None:
        await interaction.response.send_message("Server only.")
        return
        
    isLogOnlyMode = PolicyModes.get(guildId, False)
    PolicyModes[guildId] = not isLogOnlyMode
    isLogOnlyMode = PolicyModes[guildId]
    
    await interaction.response.send_message(f"Execution Policy has changed to {'`LogOnly`' if isLogOnlyMode else '`Enforced`'}")

@bot.tree.command(name="getpolicy", description="Query current policy.")
async def getpolicy(interaction: discord.Interaction):
    guildId = interaction.guild_id
    if guildId is None:
        await interaction.response.send_message("Server only.")
        return
        
    isLogOnlyMode = PolicyModes.get(guildId, False)
    await interaction.response.send_message(f"The current policy was set to: {'`LogOnly`' if isLogOnlyMode else '`Enforced`'}")

@bot.tree.command(name="getban", description="Query users banned during bot runtime.")
async def getBan(interaction: discord.Interaction):
    if not bannedUsers:
        await interaction.response.send_message("No data.")
        return
    bannedList = ", ".join(bannedUsers)
    await interaction.response.send_message(f"Banned during runtime: {bannedList}.")

@bot.tree.command(name="info", description="About BIBC...")
async def info(interaction: discord.Interaction):
    currentDuration = datetime.datetime.now(datetime.timezone.utc) - startTime
    totalSeconds = int(currentDuration.total_seconds())
    hours, remainder = divmod(totalSeconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    
    guildId = interaction.guild_id
    currentPolicy = "N/A (DMs)"
    if guildId is not None:
        isLogOnlyMode = PolicyModes.get(guildId, False)
        currentPolicy = "`LogOnly`" if isLogOnlyMode else "`Enforced`"

    bannedCount = len(bannedUsers)
    
    infoEmbed = discord.Embed(title="About BanInBlacklistedChannels Bot...")
    infoEmbed.add_field(name="Bot ID", value=f"`{str(bot.user.id)}`", inline=False)
    infoEmbed.add_field(name="Execution Policy", value=currentPolicy, inline=False)
    infoEmbed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=False)
    infoEmbed.add_field(name="Source Code", value="https://github.com/MeowIce/bibc", inline=False)
    infoEmbed.add_field(name="Banned Since Runtime", value=str(bannedCount), inline=False)
    
    await interaction.response.send_message(embed=infoEmbed)
@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    if message.channel.id in ChID:
        currentTimeStr = datetime.datetime.now().strftime('%H:%M:%S %d/%m/%Y')
        print(f"{currentTimeStr} | Message detected from @{message.author} in channel '#{message.channel.name}' (ID: {message.channel.id}). Content: {message.content}")
        
        guildId = message.guild.id if message.guild else None
        if guildId is None:
            await bot.process_commands(message)
            return
            
        isLogOnlyMode = PolicyModes.get(guildId, False)
        actionTaken = "Logged"
        
        if isLogOnlyMode:
            print(f"{currentTimeStr} | No actions were taken for @{message.author} because run mode is set to LogOnly for server {guildId}.")
        else:
            try:
                await message.guild.ban(
                    message.author,
                    reason=actionReason,
                    delete_message_seconds=300
                )
                print(f"{currentTimeStr} | Action taken for @{message.author}")
                bannedUsers.append(f"{message.author} (ID: {message.author.id})")
                actionTaken = "Banned"
            except Exception as e:
                print(f"{currentTimeStr} | Failed to take action for {message.author}: {e}")
                actionTaken = f"Failed: {e}"

        reportChannel = None
        for channelId in reportChID:
            reportChannel = message.guild.get_channel(channelId)
            if reportChannel:
                break

        if reportChannel:
            reportEmbed = discord.Embed(title="BanInBlacklistedChannels Event Log")
            reportEmbed.add_field(name="User", value=f"{message.author.mention} ({message.author.id})", inline=False)
            reportEmbed.add_field(name="Status", value=actionTaken, inline=False)
            reportEmbed.add_field(name="Content", value=message.content, inline=False)
            reportEmbed.set_footer(text=currentTimeStr)
            await reportChannel.send(embed=reportEmbed)
                
    await bot.process_commands(message)

print("BIBC is starting...")
bot.run(botToken, log_handler=None)
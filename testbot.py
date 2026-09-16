import datetime
import discord
from discord.ext import commands

botToken = ""
ChID = [123456789, 987654321]
isDebugMode = False
bannedUsers = []
startTime = datetime.datetime.now(datetime.timezone.utc)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id}).")
    print("------")

@bot.command(name="dbg")
@commands.has_permissions(administrator=True)
async def toggleDebug(ctx: commands.Context):
    global isDebugMode
    isDebugMode = not isDebugMode
    await ctx.send(f"Debug mode has changed to {'`DEBUG`' if isDebugMode else '`NORMAL`'}")

@bot.command(name="getmode")
async def getMode(ctx: commands.Context):
    await ctx.send(f"Mode: {'`DEBUG`' if isDebugMode else '`NORMAL`'}")

@bot.command(name="getban")
async def getBan(ctx: commands.Context):
    if not bannedUsers:
        await ctx.send("No data.")
        return
    bannedList = ", ".join(bannedUsers)
    await ctx.send(f"Banned during runtime: {bannedList}.")
@bot.command(name="uptime")
async def uptime(ctx: commands.Context):
    currentDuration = datetime.datetime.now(datetime.timezone.utc) - startTime
    totalSeconds = int(currentDuration.total_seconds())
    hours, remainder = divmod(totalSeconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    await ctx.send(f"{datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")} up {days}d {hours}h {minutes}m {seconds}s")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    
    if message.channel.id in ChID:
        print(f"{datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")} | Message detected from @{message.author} in channel '#{message.channel.name}' (ID: {message.channel.id}). Content: {message.content}")
        
        if isDebugMode:
            print(f"{datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")} | No actions were taken for @{message.author} because run mode is set to DEBUG.")
            await bot.process_commands(message)
            return

        try:
            await message.guild.ban(
                message.author,
                reason="gửi tin nhắn vào kênh lọc spam",
                delete_message_seconds=300
            )
            print(f"{datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")} | Action taken for @{message.author}")
            bannedUsers.append(f"{message.author} (ID: {message.author.id})")
            await message.delete()
        except Exception as e:
            print(f"{datetime.datetime.now().strftime("%H:%M:%S %d/%m/%Y")} | Failed to take action for {message.author}: {e}")
            
    await bot.process_commands(message)

bot.run(botToken)
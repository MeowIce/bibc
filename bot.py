import discord
from discord.ext import commands

# ==== CONFIG ====
botToken = ""   # Replace with bot token
ChID = ""  # Replace with channel ID
# =================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id}). Now watching {ChID}")
    print("------")

@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return
    if message.channel.id == ChID:
        try:
            await message.guild.ban(
                message.author,
                reason="gửi tin nhắn vào kênh lọc spam",
                delete_message_seconds=300
            )
            print(f"Banned {message.author}. Content: {message.content}")
            await message.delete()
        except Exception as e:
            print(f"Failed to ban {message.author}: {e}")
    await bot.process_commands(message)

bot.run(botToken)

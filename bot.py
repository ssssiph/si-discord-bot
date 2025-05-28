import os
import discord
from discord.ext import commands
from db import get_prefix, init_db
from commands import setup_commands
from dotenv import load_dotenv

load_dotenv()
init_db()

intents = discord.Intents.default()
intents.message_content = True

def get_prefix_callable(bot, message):
    if not message.guild:
        return "s!"
    return get_prefix(message.guild.id)

bot = commands.Bot(command_prefix=get_prefix_callable, intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Бот запущен как {bot.user}!")

setup_commands(bot)

bot.run(os.getenv("DISCORD_TOKEN"))

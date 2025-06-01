import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.db import get_prefix

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=intents, help_command=None)

    async def get_prefix(self, bot, message):
        """Получение префикса из базы"""
        return get_prefix(message.guild.id) if message.guild else "!"

    async def setup_hook(self):
        """Загружаем команды"""
        await self.load_extension("commands.core")
        await self.load_extension("commands.marriage")
        await self.load_extension("commands.verification")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    await bot.tree.sync()

bot.run(os.getenv("DISCORD_TOKEN"))

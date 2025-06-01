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
        """Загружаем команды, проверяем ошибки"""
        try:
            print("🟡 Загружаю core.py...")
            await self.load_extension("commands.core")
            print("✅ core.py загружен!")

            print("🟡 Загружаю marriage.py...")
            await self.load_extension("commands.marriage")
            print("✅ marriage.py загружен!")

            print("🟡 Загружаю verification.py...")
            await self.load_extension("commands.verification")
            print("✅ verification.py загружен!")

        except Exception as e:
            print(f"❌ Ошибка при загрузке расширений: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    await bot.tree.sync()

    print("📜 Зарегистрированные команды:")
    for command in bot.commands:
        print(f"- {command.name}")

bot.run(os.getenv("DISCORD_TOKEN"))

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

    def get_prefix(self, bot, message):
        """Получение префикса из базы"""
        return get_prefix(message.guild.id) if message.guild else "s!"

    async def setup_hook(self):
        """Загружаем команды, регистрируем слэш-команды"""
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

            print("📜 Регистрирую слэш-команды...")
            bot.tree.add_command(bot.get_command("setup"))
            bot.tree.add_command(bot.get_command("help"))
            bot.tree.add_command(bot.get_command("ping"))
            bot.tree.add_command(bot.get_command("sync"))
            
            await bot.tree.sync()
            print("✅ Слэш-команды синхронизированы!")

        except Exception as e:
            print(f"❌ Ошибка при загрузке расширений: {e}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')

bot.run(os.getenv("DISCORD_TOKEN"))

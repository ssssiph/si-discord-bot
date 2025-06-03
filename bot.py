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
        super().__init__(
            command_prefix=self.get_prefix,
            intents=intents,
            help_command=None,
            case_insensitive=True
        )

    async def get_prefix(self, message):
        """Получение префикса из базы"""
        return get_prefix(message.guild.id) if message.guild else "s!"

    async def setup_hook(self):
        """Загружаем расширения и синхронизируем команды"""
        try:
            print("🟡 Загружаю commands...")
            await self.load_extension("commands")
            print("✅ commands загружен!")

            print("📜 Синхронизирую слэш-команды...")
            await self.tree.sync()
            print("✅ Слэш-команды синхронизированы!")

        except Exception as e:
            print(f"❌ Ошибка при загрузке расширений: {e}")

    async def on_command_error(self, ctx, error):
        """Обработка ошибок команд"""
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ У вас недостаточно прав!")
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            print(f"Ошибка команды: {error}")
            await ctx.reply(f"❌ Произошла ошибка: {error}")

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')

bot.run(os.getenv("DISCORD_TOKEN"))

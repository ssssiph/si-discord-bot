import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from db.get_prefix import get_prefix

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
        try:
            prefix = get_prefix(message.guild.id) if message.guild else "s!"
            print(f"Префикс для сервера {message.guild.id if message.guild else 'DM'}: {prefix}")
            return prefix
        except Exception as e:
            print(f"Ошибка получения префикса: {e}")
            return "s!"

    async def setup_hook(self):
        """Загружаем расширения"""
        try:
            print("🟡 Загружаю commands...")
            await self.load_extension("commands")
            print("✅ commands загружен!")
        except Exception as e:
            print(f"❌ Ошибка при загрузке расширений: {e}")
            raise

    async def on_command_error(self, ctx, error):
        """Обработка ошибок текстовых команд"""
        print(f"Ошибка команды: {error}")
        if isinstance(error, commands.MissingPermissions):
            await ctx.reply("❌ У вас нет прав администратора!")
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            await ctx.reply(f"❌ Произошла ошибка: {error}")

    async def on_slash_command_error(self, interaction, error):
        """Обработка ошибок слэш-команд"""
        print(f"Ошибка слэш-команды: {error}")
        if not interaction.response.is_done():
            if isinstance(error, commands.MissingPermissions):
                await interaction.response.send_message("❌ У вас нет прав администратора!", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ Произошла ошибка: {error}", ephemeral=True)

bot = MyBot()

@bot.event
async def on_ready():
    print(f'✅ Бот {bot.user} запущен!')
    try:
        print("📜 Синхронизирую слэш-команды...")
        synced = await bot.tree.sync()
        print(f"✅ Синхронизировано {len(synced)} слэш-команд: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"❌ Ошибка синхронизации: {e}")

bot.run(os.getenv("DISCORD_TOKEN"))

import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from get_prefix import get_prefix_db
from set_prefix import set_prefix_db

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True

async def get_prefix(bot, message):
    if message.guild:
        return get_prefix_db(message.guild.id)
    return "s!"

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Бот {bot.user} готов. Слэш-команды синхронизированы глобально.")

# ========= Слэш-команда: /ping =========
@bot.tree.command(name="ping", description="Показывает пинг бота")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"🏓 Пинг: {latency}мс")

# ========= Слэш-команда: /prefix <новый> =========
@bot.tree.command(name="prefix", description="Изменить префикс бота для этого сервера")
@app_commands.describe(new_prefix="Новый префикс")
async def change_prefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ Только администратор может менять префикс.", ephemeral=True)
        return
    set_prefix_db(interaction.guild.id, new_prefix)
    await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

# ========= Обычная команда =========
@bot.command(name="ping")
async def ping_command(ctx):
    latency = round(bot.latency * 1000)
    await ctx.send(f"🏓 Пинг: {latency}мс")

bot.run(os.getenv("DISCORD_TOKEN"))

import discord
from discord.ext import commands
from discord import app_commands
import mysql.connector
import os

# Получение переменных окружения
TOKEN = os.getenv("DISCORD_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

# Установка соединения с БД
def get_db_connection():
    return mysql.connector.connect(
        host=DB_URL.split('@')[1].split('/')[0].split(':')[0],
        port=DB_URL.split('@')[1].split('/')[0].split(':')[1],
        user=DB_URL.split('//')[1].split(':')[0],
        password=DB_URL.split('//')[1].split(':')[1].split('@')[0],
        database=DB_URL.split('/')[-1]
    )

# Получение префикса из базы
def get_prefix_db(guild_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS prefixes (guild_id BIGINT PRIMARY KEY, prefix VARCHAR(10))")
    conn.commit()

    cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else "s!"

# Установка префикса в базу
def set_prefix_db(guild_id, prefix):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (guild_id, prefix))
    conn.commit()
    conn.close()

# Функция получения префикса
def get_prefix(bot, message):
    if not message.guild:
        return "s!"
    return get_prefix_db(message.guild.id)

# Настройка интентов
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# Создание экземпляра бота
bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# ========== ОБЫЧНЫЕ КОМАНДЫ ==========
@bot.command(name="ping")
async def ping_command(ctx):
    await ctx.send(f"🏓 Пинг: {round(bot.latency * 1000)} мс")

# ========== СЛЭШ КОМАНДЫ ==========

@bot.tree.command(name="ping", description="Проверка пинга бота")
async def ping_slash(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Пинг: {round(bot.latency * 1000)} мс")

@bot.tree.command(name="prefix", description="Изменить префикс бота")
@app_commands.describe(new_prefix="Новый префикс (например, !)")
async def prefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.guild:
        await interaction.response.send_message("❌ Эта команда работает только на сервере.", ephemeral=True)
        return

    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("❌ У вас нет прав администратора.", ephemeral=True)
        return

    set_prefix_db(interaction.guild.id, new_prefix)
    await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

# Синхронизация команд
@bot.event
async def on_ready():
    print(f"✅ Бот {bot.user} запущен.")
    for guild in bot.guilds:
        try:
            await bot.tree.sync(guild=discord.Object(id=guild.id))
            print(f"🔁 Слэш-команды синхронизированы на сервере: {guild.name}")
        except Exception as e:
            print(f"❌ Ошибка при синхронизации слэш-команд на {guild.name}: {e}")

# Запуск бота
bot.run(TOKEN)

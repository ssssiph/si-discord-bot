import discord
from discord.ext import commands
from discord import app_commands
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DB_URL = os.getenv("DATABASE_URL")

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True

bot = commands.Bot(command_prefix="s!", intents=intents, help_command=None)
tree = bot.tree

# =================== DATABASE ===================
import re
import urllib.parse as up

parsed = re.match(r"mysql:\/\/(?P<user>.*?):(?P<password>.*?)@(?P<host>.*?):(?P<port>\d+)\/(?P<db>.+)", DB_URL)
conn = mysql.connector.connect(
    user=parsed.group("user"),
    password=parsed.group("password"),
    host=parsed.group("host"),
    port=parsed.group("port"),
    database=parsed.group("db"),
)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS prefixes (
    guild_id BIGINT PRIMARY KEY,
    prefix VARCHAR(10) DEFAULT 's!'
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS marriages (
    user_id BIGINT,
    partner_id BIGINT,
    PRIMARY KEY (user_id, partner_id)
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS marriage_limits (
    user_id BIGINT PRIMARY KEY,
    limit_count INT DEFAULT 10
)
""")
conn.commit()

# ========== PREFIX GETTER ==========
async def get_prefix(bot, message):
    if not message.guild:
        return "s!"
    cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = %s", (message.guild.id,))
    result = cursor.fetchone()
    return result[0] if result else "s!"

bot.command_prefix = get_prefix

# =================== EVENTS ===================
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        synced = await tree.sync()
        print(f'Synced {len(synced)} command(s)')
    except Exception as e:
        print(e)

# =================== PREFIX COMMANDS ===================
@bot.command(name='prefix')
@commands.has_permissions(administrator=True)
async def change_prefix(ctx, new_prefix: str):
    cursor.execute("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (ctx.guild.id, new_prefix))
    conn.commit()
    await ctx.send(f"Префикс изменён на `{new_prefix}`")

@tree.command(name="prefix", description="Изменить префикс команд")
@app_commands.describe(prefix="Новый префикс")
@app_commands.checks.has_permissions(administrator=True)
async def slash_prefix(interaction: discord.Interaction, prefix: str):
    cursor.execute("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (interaction.guild.id, prefix))
    conn.commit()
    await interaction.response.send_message(f"Префикс изменён на `{prefix}`")

# =================== HELP ===================
@bot.command(name="help")
async def help_cmd(ctx):
    prefix = await get_prefix(bot, ctx.message)
    help_text = f"""📖 **Информация о боте**
Префикс: `{prefix}`
Сервер поддержки: https://discord.gg/g24dUqCxjt

**Команды:**
{prefix}help - Показать это сообщение
{prefix}prefix <префикс> - Изменить префикс (только для админов)
{prefix}ping - Проверка пинга
{prefix}marriage marry <пользователь> - Предложить брак
{prefix}marriage accept <пользователь> - Принять предложение
{prefix}marriage decline <пользователь> - Отклонить
{prefix}marriage divorce <пользователь> - Развод
{prefix}marriage info - Информация о браках
{prefix}marriage list - Мои партнёры
{prefix}marriage proposals - Полученные предложения
"""
    await ctx.send(help_text)

@tree.command(name="help", description="Показать справку по боту")
async def slash_help(interaction: discord.Interaction):
    prefix = await get_prefix(bot, interaction)
    await interaction.response.send_message(f"""📖 **Информация о боте**
Префикс: `{prefix}`
Сервер поддержки: https://discord.gg/g24dUqCxjt

**Слэш-команды:** `/ping`, `/prefix`, `/help`, `/marriage ...`
**Префикс-команды:** `s!ping`, `s!prefix`, `s!marriage ...`
""")

# =================== PING ===================
@bot.command(name='ping')
async def ping(ctx):
    await ctx.send(f'Пинг: {round(bot.latency * 1000)}мс')

@tree.command(name="ping", description="Проверить пинг бота")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f'Пинг: {round(bot.latency * 1000)}мс')

# =================== MARRIAGE ===================
marriage = app_commands.Group(name="marriage", description="Брачные команды")
tree.add_command(marriage)

@bot.group(name="marriage")
async def marriage_group(ctx):
    if ctx.invoked_subcommand is None:
        await ctx.send("Используй подкоманды: info, marry, accept, decline, divorce, list, proposals")

# marry
@marriage.command(name="marry", description="💍 Отправьте предложение о браке кому-то")
@app_commands.describe(member="Пользователь")
async def marry(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        return await interaction.response.send_message("Вы не можете жениться на себе", ephemeral=True)

    cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = %s", (interaction.user.id,))
    current = cursor.fetchone()[0]

    cursor.execute("SELECT limit_count FROM marriage_limits WHERE user_id = %s", (interaction.user.id,))
    limit = cursor.fetchone()
    max_partners = limit[0] if limit else 10

    if current >= max_partners:
        return await interaction.response.send_message(f"Вы достигли лимита браков ({max_partners})", ephemeral=True)

    cursor.execute("INSERT IGNORE INTO marriages (user_id, partner_id) VALUES (%s, %s)", (interaction.user.id, member.id))
    conn.commit()
    await interaction.response.send_message(f"{interaction.user.mention} предложил брак {member.mention} 💍")

@marriage_group.command(name="marry")
async def marry_cmd(ctx, member: discord.Member):
    await marry.callback(ctx, member)

# accept
@marriage.command(name="accept", description="💍 Принять предложение о браке")
@app_commands.describe(user="Пользователь")
async def accept(interaction: discord.Interaction, user: discord.User):
    cursor.execute("SELECT * FROM marriages WHERE user_id = %s AND partner_id = %s", (user.id, interaction.user.id))
    if cursor.fetchone():
        cursor.execute("INSERT IGNORE INTO marriages (user_id, partner_id) VALUES (%s, %s)", (interaction.user.id, user.id))
        conn.commit()
        await interaction.response.send_message(f"{interaction.user.mention} принял брак с {user.mention}")
    else:
        await interaction.response.send_message("Нет предложения от этого пользователя", ephemeral=True)

@marriage_group.command(name="accept")
async def accept_cmd(ctx, user: discord.User):
    await accept.callback(ctx, user)

# decline
@marriage.command(name="decline", description="💍 Отклонить предложение о браке")
@app_commands.describe(user="Пользователь")
async def decline(interaction: discord.Interaction, user: discord.User):
    cursor.execute("DELETE FROM marriages WHERE user_id = %s AND partner_id = %s", (user.id, interaction.user.id))
    conn.commit()
    await interaction.response.send_message(f"{interaction.user.mention} отклонил предложение от {user.mention}")

@marriage_group.command(name="decline")
async def decline_cmd(ctx, user: discord.User):
    await decline.callback(ctx, user)

# divorce
@marriage.command(name="divorce", description="💍 Развестись с кем-то")
@app_commands.describe(user="Пользователь")
async def divorce(interaction: discord.Interaction, user: discord.User):
    cursor.execute("DELETE FROM marriages WHERE (user_id = %s AND partner_id = %s) OR (user_id = %s AND partner_id = %s)", (interaction.user.id, user.id, user.id, interaction.user.id))
    conn.commit()
    await interaction.response.send_message(f"{interaction.user.mention} развёлся с {user.mention}")

@marriage_group.command(name="divorce")
async def divorce_cmd(ctx, user: discord.User):
    await divorce.callback(ctx, user)

# list
@marriage.command(name="list", description="💍 Просмотреть свои браки")
async def list_marriages(interaction: discord.Interaction):
    cursor.execute("SELECT partner_id FROM marriages WHERE user_id = %s", (interaction.user.id,))
    partners = cursor.fetchall()
    if not partners:
        await interaction.response.send_message("У вас пока нет партнёров.")
        return
    mentions = [f"<@{p[0]}>" for p in partners]
    await interaction.response.send_message("Ваши партнёры: " + ", ".join(mentions))

@marriage_group.command(name="list")
async def list_cmd(ctx):
    await list_marriages.callback(ctx)

# proposals
@marriage.command(name="proposals", description="💍 Посмотреть свои предложения")
@app_commands.describe(page="Страница")
async def proposals(interaction: discord.Interaction, page: int = 1):
    cursor.execute("SELECT user_id FROM marriages WHERE partner_id = %s", (interaction.user.id,))
    proposals = cursor.fetchall()
    if not proposals:
        await interaction.response.send_message("У вас нет предложений.")
        return
    mentions = [f"<@{p[0]}>" for p in proposals]
    await interaction.response.send_message("Предложения: " + ", ".join(mentions))

@marriage_group.command(name="proposals")
async def proposals_cmd(ctx, page: int = 1):
    await proposals.callback(ctx, page)

# =================== RUN ===================
bot.run(TOKEN)

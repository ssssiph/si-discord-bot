import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from datetime import datetime
import sqlite3

DEFAULT_PREFIX = "s!"
SUPPORT_SERVER = "https://discord.gg/g24dUqCxjt"
DEFAULT_MARRIAGE_LIMIT = 1

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=intents, help_command=None)
        self.db = sqlite3.connect("bot.db")
        self.cursor = self.db.cursor()
        self.create_tables()

    async def setup_hook(self):
        await self.tree.sync()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixes (
            guild_id INTEGER PRIMARY KEY,
            prefix TEXT
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriages (
            user_id INTEGER,
            partner_id INTEGER,
            timestamp TEXT,
            PRIMARY KEY(user_id, partner_id)
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriage_limits (
            user_id INTEGER PRIMARY KEY,
            marriage_limit INTEGER DEFAULT 1
        )
        """)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriage_proposals (
            proposer_id INTEGER,
            target_id INTEGER,
            timestamp TEXT,
            PRIMARY KEY(proposer_id, target_id)
        )
        """)
        self.db.commit()

    async def get_prefix(self, message):
        return DEFAULT_PREFIX

bot = MyBot()

@bot.tree.command(name="prefix", description="Изменить префикс команд")
@app_commands.describe(new_prefix="Новый префикс")
async def changeprefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("⛔ Только администратор может менять префикс.", ephemeral=True)
    await interaction.response.send_message(f"❌ Префикс менять нельзя, он всегда `{DEFAULT_PREFIX}`.", ephemeral=True)

HELP_COMMANDS = {
    "help": "Показать это сообщение",
    "prefix": "Изменить префикс команд",
    "marriage info": "💍 Информация про брак",
    "marriage accept <user>": "💍 Принять предложение о браке",
    "marriage decline <user>": "💍 Отклонить предложение о браке",
    "marriage divorce <user>": "💍 Развестись с кем-то",
    "marriage list": "💍 Просмотреть свои браки",
    "marriage marry <member>": "💍 Отправить предложение о браке кому-то",
    "marriage proposals [page]": "💍 Посмотреть предложения браков"
}

async def send_help(ctx_or_interaction):
    prefix = DEFAULT_PREFIX
    embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)
    embed.add_field(name="Префикс", value=f"`{prefix}`", inline=False)
    embed.add_field(name="Сервер поддержки", value=SUPPORT_SERVER, inline=False)
    commands_text = "\n".join(f"`{prefix}{cmd}` - {desc}" for cmd, desc in HELP_COMMANDS.items())
    embed.add_field(name="Доступные команды", value=commands_text, inline=False)
    embed.set_footer(text="Спасибо, что используете нашего бота 💙")

    if isinstance(ctx_or_interaction, commands.Context):
        await ctx_or_interaction.send(embed=embed)
    else:
        await ctx_or_interaction.response.send_message(embed=embed)

@bot.command(name="help")
async def helpcmd(ctx):
    await send_help(ctx)

@bot.tree.command(name="help", description="Показать помощь по командам")
async def helpslash(interaction: discord.Interaction):
    await send_help(interaction)

marriage = app_commands.Group(name="marriage", description="Команды связанные с браком")

@marriage.command(name="info", description="Информация о браке")
async def marriageinfo(interaction: discord.Interaction):
    description = (
        "💍 **Что такое брак?**\n"
        "Брак — это связь между двумя пользователями, позволяющая им использовать специальные команды и функции.\n"
        "Вы можете предлагать брак, принимать или отклонять предложения, разводиться и просматривать список своих партнёров."
    )
    embed = discord.Embed(title="💍 Информация о браке", description=description, color=0xF47FFF)
    await interaction.response.send_message(embed=embed)

@marriage.command(name="list", description="Показать список ваших браков")
async def marriagelist(interaction: discord.Interaction):
    bot.cursor.execute("SELECT partner_id, timestamp FROM marriages WHERE user_id = ?", (interaction.user.id,))
    marriages = bot.cursor.fetchall()
    if not marriages:
        return await interaction.response.send_message("💔 У вас нет браков.")
    embed = discord.Embed(title="💍 Ваши браки", color=0xF47FFF)
    for partner_id, timestamp in marriages:
        partner = interaction.guild.get_member(partner_id)
        name = partner.display_name if partner else f"Unknown ({partner_id})"
        dt = datetime.fromisoformat(timestamp)
        embed.add_field(name=name, value=f"В браке с <t:{int(dt.timestamp())}:R>", inline=False)
    await interaction.response.send_message(embed=embed)

@marriage.command(name="marry", description="Предложить пользователю вступить в брак")
@app_commands.describe(member="Пользователь")
async def marriagemarry(interaction: discord.Interaction, member: discord.Member):
    if member.id == interaction.user.id:
        return await interaction.response.send_message("❌ Вы не можете жениться на себе.", ephemeral=True)
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (interaction.user.id,))
    result = bot.cursor.fetchone()
    marriage_limit = result[0] if result else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (interaction.user.id,))
    count = bot.cursor.fetchone()[0]
    if count >= marriage_limit:
        return await interaction.response.send_message(f"❌ У вас уже максимальное количество партнёров ({marriage_limit}).", ephemeral=True)
    bot.cursor.execute("SELECT 1 FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (interaction.user.id, member.id))
    if bot.cursor.fetchone():
        return await interaction.response.send_message("❗ Вы уже отправляли предложение этому пользователю.", ephemeral=True)
    now = datetime.utcnow().isoformat()
    bot.cursor.execute("INSERT INTO marriage_proposals (proposer_id, target_id, timestamp) VALUES (?, ?, ?)",
                       (interaction.user.id, member.id, now))
    bot.db.commit()
    embed = discord.Embed(title="💍 Предложение руки и сердца!", color=0xF47FFF)
    embed.add_field(name="Кто предлагает", value=interaction.user.mention, inline=True)
    embed.add_field(name="Кому", value=member.mention, inline=True)
    embed.set_footer(text="Чтобы подтвердить, используйте команду /marriage accept")
    await interaction.response.send_message(embed=embed)

@marriage.command(name="accept", description="Принять предложение о браке")
@app_commands.describe(user="Пользователь, чьё предложение вы принимаете")
async def marriageaccept(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("SELECT timestamp FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?",
                       (user.id, interaction.user.id))
    result = bot.cursor.fetchone()
    if not result:
        return await interaction.response.send_message("❌ У этого пользователя нет предложения для вас.", ephemeral=True)
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (interaction.user.id,))
    target_limit = bot.cursor.fetchone()
    target_limit = target_limit[0] if target_limit else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (interaction.user.id,))
    if bot.cursor.fetchone()[0] >= target_limit:
        return await interaction.response.send_message("❌ Вы достигли лимита браков.", ephemeral=True)
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (user.id,))
    proposer_limit = bot.cursor.fetchone()
    proposer_limit = proposer_limit[0] if proposer_limit else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (user.id,))
    if bot.cursor.fetchone()[0] >= proposer_limit:
        return await interaction.response.send_message("❌ Этот пользователь достиг лимита браков.", ephemeral=True)
    now = datetime.utcnow().isoformat()
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (interaction.user.id, user.id, now))
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (user.id, interaction.user.id, now))
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message(f"💍 Поздравляем! Вы теперь в браке с {user.mention}")

@marriage.command(name="decline", description="Отклонить предложение о браке")
@app_commands.describe(user="Пользователь, чьё предложение вы отклоняете")
async def marriagedecline(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message("✅ Предложение отклонено.")

@marriage.command(name="divorce", description="Развестись с пользователем")
@app_commands.describe(user="Партнёр, с которым вы хотите развестись")
async def marriagedivorce(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("DELETE FROM marriages WHERE user_id = ? AND partner_id = ?", (interaction.user.id, user.id))
    bot.cursor.execute("DELETE FROM marriages WHERE user_id = ? AND partner_id = ?", (user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message(f"💔 Вы развелись с {user.mention}.")

@marriage.command(name="proposals", description="Посмотреть предложения о браке")
@app_commands.describe(page="Страница (по 10 предложений)")
async def marriageproposals(interaction: discord.Interaction, page: int = 1):
    bot.cursor.execute("SELECT proposer_id, timestamp FROM marriage_proposals WHERE target_id = ?", (interaction.user.id,))
    proposals = bot.cursor.fetchall()
    if not proposals:
        return await interaction.response.send_message("📭 У вас нет предложений о браке.")
    per_page = 10
    start = (page - 1) * per_page
    end = start + per_page
    embed = discord.Embed(title="💌 Предложения о браке", color=0xF47FFF)
    for proposer_id, timestamp in proposals[start:end]:
        proposer = interaction.guild.get_member(proposer_id)
        name = proposer.display_name if proposer else f"Unknown ({proposer_id})"
        dt = datetime.fromisoformat(timestamp)
        embed.add_field(name=name, value=f"Предложено <t:{int(dt.timestamp())}:R>", inline=False)
    embed.set_footer(text=f"Страница {page}/{(len(proposals) - 1) // per_page + 1}")
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(marriage)

bot.run(os.getenv("DISCORD_TOKEN"))

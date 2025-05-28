import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from datetime import datetime
import sqlite3

# ─── Базовые настройки ────────────────────────────
DEFAULT_PREFIX = "s!"
SUPPORT_SERVER = "https://discord.gg/g24dUqCxjt"
DEFAULT_MARRIAGE_LIMIT = 1

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

class MyBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, intents=intents)
        self.prefixes = {}
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
        if message.guild:
            prefix = self.prefixes.get(message.guild.id)
            if not prefix:
                self.cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = ?", (message.guild.id,))
                result = self.cursor.fetchone()
                prefix = result[0] if result else DEFAULT_PREFIX
                self.prefixes[message.guild.id] = prefix
            return prefix
        return DEFAULT_PREFIX

bot = MyBot()

# ─── Команда /prefix ──────────────────────────
@bot.tree.command(name="prefix", description="Изменить префикс команд")
@app_commands.describe(new_prefix="Новый префикс")
async def change_prefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("⛔ Только администратор может менять префикс.", ephemeral=True)

    bot.prefixes[interaction.guild.id] = new_prefix
    bot.cursor.execute("REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)", (interaction.guild.id, new_prefix))
    bot.db.commit()
    await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

# ─── Команда help ───────────────────────
HELP_COMMANDS = {
    "help": "Показать это сообщение",
    "prefix": "Изменить префикс команд",
    "marriage info": "💍 Информация про браки",
    "marriage accept <user>": "💍 Принять предложение о браке",
    "marriage decline <user>": "💍 Отклонить предложение о браке",
    "marriage divorce <user>": "💍 Развестись с кем-то",
    "marriage list": "💍 Просмотреть свои браки",
    "marriage marry <member>": "💍 Отправить предложение о браке кому-то",
    "marriage proposals [page]": "💍 Посмотреть предложения браков"
}

async def send_help(ctx_or_interaction):
    if isinstance(ctx_or_interaction, commands.Context):
        prefix = await bot.get_prefix(ctx_or_interaction.message)
    else:
        prefix = bot.prefixes.get(ctx_or_interaction.guild.id, DEFAULT_PREFIX)

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
async def help_command(ctx):
    await send_help(ctx)

@bot.tree.command(name="help", description="Показать помощь по командам")
async def help_slash(interaction: discord.Interaction):
    await send_help(interaction)

# ─── /marriage info ────────────────────────────────
@bot.tree.command(name="marriage_info", description="Показать список ваших браков")
async def marriage_info(interaction: discord.Interaction):
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

@bot.command(name="marriage_info")
async def marriage_info_cmd(ctx):
    class DummyInteraction:
        def __init__(self, user, guild):
            self.user = user
            self.guild = guild
        async def response(self):
            pass
    dummy = DummyInteraction(ctx.author, ctx.guild)
    dummy.response = ctx
    await marriage_info(dummy)

# ─── Команда marry ─────────────────────────────────
@bot.tree.command(name="marriage_marry", description="Предложить пользователю вступить в брак")
@app_commands.describe(member="Пользователь")
async def marriage_marry(interaction: discord.Interaction, member: discord.Member):
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
    embed.set_footer(text="Чтобы подтвердить, используйте команду /marriage_accept")

    await interaction.response.send_message(embed=embed)

# ─── Команда marriage_accept ────────────────────────────────
@bot.tree.command(name="marriage_accept", description="Принять предложение о браке")
@app_commands.describe(user="Пользователь, чьё предложение вы принимаете")
async def marriage_accept(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("SELECT timestamp FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?",
                       (user.id, interaction.user.id))
    result = bot.cursor.fetchone()
    if not result:
        return await interaction.response.send_message("❌ У этого пользователя нет предложения для вас.", ephemeral=True)

    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (interaction.user.id,))
    target_marriage_limit = bot.cursor.fetchone()
    target_marriage_limit = target_marriage_limit[0] if target_marriage_limit else DEFAULT_MARRIAGE_LIMIT

    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (interaction.user.id,))
    target_marriages = bot.cursor.fetchone()[0]

    if target_marriages >= target_marriage_limit:
        return await interaction.response.send_message("❌ Вы достигли лимита браков.", ephemeral=True)

    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (user.id,))
    proposer_marriage_limit = bot.cursor.fetchone()
    proposer_marriage_limit = proposer_marriage_limit[0] if proposer_marriage_limit else DEFAULT_MARRIAGE_LIMIT

    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (user.id,))
    proposer_marriages = bot.cursor.fetchone()[0]

    if proposer_marriages >= proposer_marriage_limit:
        return await interaction.response.send_message("❌ Отправитель достиг лимита браков.", ephemeral=True)

    now = datetime.utcnow().isoformat()

    bot.cursor.executemany(
        "INSERT INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)",
        [
            (interaction.user.id, user.id, now),
            (user.id, interaction.user.id, now)
        ]
    )

    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    bot.db.commit()

    await interaction.response.send_message(f"💖 {interaction.user.mention} и {user.mention} теперь в браке!")

bot.run(os.getenv("DISCORD_TOKEN"))

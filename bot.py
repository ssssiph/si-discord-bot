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

# --- /prefix ---
@bot.tree.command(name="prefix", description="Изменить префикс команд")
@app_commands.describe(new_prefix="Новый префикс")
async def change_prefix(interaction: discord.Interaction, new_prefix: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("⛔ Только администратор может менять префикс.", ephemeral=True)
    bot.prefixes[interaction.guild.id] = new_prefix
    bot.cursor.execute("REPLACE INTO prefixes (guild_id, prefix) VALUES (?, ?)", (interaction.guild.id, new_prefix))
    bot.db.commit()
    await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

# --- /help ---
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

# --- marriage group ---
marriage = app_commands.Group(name="marriage", description="Команды связанные с браком")

@marriage.command(name="info", description="Информация о браке")
async def marriage_info(interaction: discord.Interaction):
    description = (
        "💍 **Что такое брак?**\n"
        "Брак — это связь между двумя пользователями, позволяющая им использовать специальные команды и функции.\n"
        "Вы можете предлагать брак, принимать или отклонять предложения, разводиться и просматривать список своих партнёров."
    )
    embed = discord.Embed(title="💍 Информация о браке", description=description, color=0xF47FFF)
    await interaction.response.send_message(embed=embed)

@marriage.command(name="list", description="Показать список ваших браков")
async def marriage_list(interaction: discord.Interaction):
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
    embed.set_footer(text="Чтобы подтвердить, используйте команду /marriage accept")
    await interaction.response.send_message(embed=embed)

@marriage.command(name="accept", description="Принять предложение о браке")
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
        return await interaction.response.send_message("❌ Пользователь достиг лимита браков.", ephemeral=True)
    now = datetime.utcnow().isoformat()
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (interaction.user.id, user.id, now))
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (user.id, interaction.user.id, now))
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message(f"💍 Поздравляем! Вы теперь в браке с {user.mention}")

@marriage.command(name="decline", description="Отклонить предложение о браке")
@app_commands.describe(user="Пользователь, чьё предложение вы отклоняете")
async def marriage_decline(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("SELECT 1 FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    if not bot.cursor.fetchone():
        return await interaction.response.send_message("❌ У этого пользователя нет предложения для вас.", ephemeral=True)
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message(f"❌ Вы отклонили предложение от {user.mention}")

@marriage.command(name="divorce", description="Развестись с кем-то")
@app_commands.describe(user="Партнёр для развода")
async def marriage_divorce(interaction: discord.Interaction, user: discord.User):
    bot.cursor.execute("SELECT 1 FROM marriages WHERE user_id = ? AND partner_id = ?", (interaction.user.id, user.id))
    if not bot.cursor.fetchone():
        return await interaction.response.send_message("❌ У вас нет брака с этим пользователем.", ephemeral=True)
    bot.cursor.execute("DELETE FROM marriages WHERE (user_id = ? AND partner_id = ?) OR (user_id = ? AND partner_id = ?)",
                       (interaction.user.id, user.id, user.id, interaction.user.id))
    bot.db.commit()
    await interaction.response.send_message(f"💔 Вы развелись с {user.mention}")

@marriage.command(name="proposals", description="Посмотреть предложения браков")
@app_commands.describe(page="Номер страницы")
async def marriage_proposals(interaction: discord.Interaction, page: int = 1):
    limit = 5
    offset = (page - 1) * limit
    bot.cursor.execute("SELECT proposer_id, timestamp FROM marriage_proposals WHERE target_id = ? LIMIT ? OFFSET ?", (interaction.user.id, limit, offset))
    proposals = bot.cursor.fetchall()
    if not proposals:
        return await interaction.response.send_message("📭 У вас нет предложений о браке.")
    embed = discord.Embed(title=f"💍 Предложения брака - страница {page}", color=0xF47FFF)
    for proposer_id, timestamp in proposals:
        proposer = interaction.guild.get_member(proposer_id)
        name = proposer.display_name if proposer else f"Unknown ({proposer_id})"
        dt = datetime.fromisoformat(timestamp)
        embed.add_field(name=name, value=f"Отправлено <t:{int(dt.timestamp())}:R>", inline=False)
    await interaction.response.send_message(embed=embed)

bot.tree.add_command(marriage)

# --- префиксные команды marriage ---

@bot.command(name="marriage_info")
async def marriage_info_cmd(ctx):
    description = (
        "💍 **Что такое брак?**\n"
        "Брак — это связь между двумя пользователями, позволяющая им использовать специальные команды и функции.\n"
        "Вы можете предлагать брак, принимать или отклонять предложения, разводиться и просматривать список своих партнёров."
    )
    embed = discord.Embed(title="💍 Информация о браке", description=description, color=0xF47FFF)
    await ctx.send(embed=embed)

@bot.command(name="marriage_list")
async def marriage_list_cmd(ctx):
    bot.cursor.execute("SELECT partner_id, timestamp FROM marriages WHERE user_id = ?", (ctx.author.id,))
    marriages = bot.cursor.fetchall()
    if not marriages:
        return await ctx.send("💔 У вас нет браков.")
    embed = discord.Embed(title="💍 Ваши браки", color=0xF47FFF)
    for partner_id, timestamp in marriages:
        member = ctx.guild.get_member(partner_id)
        name = member.display_name if member else f"Unknown ({partner_id})"
        dt = datetime.fromisoformat(timestamp)
        embed.add_field(name=name, value=f"В браке с <t:{int(dt.timestamp())}:R>", inline=False)
    await ctx.send(embed=embed)

@bot.command(name="marriage_marry")
async def marriage_marry_cmd(ctx, member: discord.Member):
    if member.id == ctx.author.id:
        return await ctx.send("❌ Вы не можете жениться на себе.")
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (ctx.author.id,))
    result = bot.cursor.fetchone()
    marriage_limit = result[0] if result else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (ctx.author.id,))
    count = bot.cursor.fetchone()[0]
    if count >= marriage_limit:
        return await ctx.send(f"❌ У вас уже максимальное количество партнёров ({marriage_limit}).")
    bot.cursor.execute("SELECT 1 FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (ctx.author.id, member.id))
    if bot.cursor.fetchone():
        return await ctx.send("❗ Вы уже отправляли предложение этому пользователю.")
    now = datetime.utcnow().isoformat()
    bot.cursor.execute("INSERT INTO marriage_proposals (proposer_id, target_id, timestamp) VALUES (?, ?, ?)",
                       (ctx.author.id, member.id, now))
    bot.db.commit()
    await ctx.send(f"💍 Вы отправили предложение о браке {member.mention}!")

@bot.command(name="marriage_accept")
async def marriage_accept_cmd(ctx, user: discord.User):
    bot.cursor.execute("SELECT timestamp FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, ctx.author.id))
    result = bot.cursor.fetchone()
    if not result:
        return await ctx.send("❌ У этого пользователя нет предложения для вас.")
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (ctx.author.id,))
    target_marriage_limit = bot.cursor.fetchone()
    target_marriage_limit = target_marriage_limit[0] if target_marriage_limit else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (ctx.author.id,))
    target_marriages = bot.cursor.fetchone()[0]
    if target_marriages >= target_marriage_limit:
        return await ctx.send("❌ Вы достигли лимита браков.")
    bot.cursor.execute("SELECT marriage_limit FROM marriage_limits WHERE user_id = ?", (user.id,))
    proposer_marriage_limit = bot.cursor.fetchone()
    proposer_marriage_limit = proposer_marriage_limit[0] if proposer_marriage_limit else DEFAULT_MARRIAGE_LIMIT
    bot.cursor.execute("SELECT COUNT(*) FROM marriages WHERE user_id = ?", (user.id,))
    proposer_marriages = bot.cursor.fetchone()[0]
    if proposer_marriages >= proposer_marriage_limit:
        return await ctx.send("❌ Пользователь достиг лимита браков.")
    now = datetime.utcnow().isoformat()
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (ctx.author.id, user.id, now))
    bot.cursor.execute("INSERT OR IGNORE INTO marriages (user_id, partner_id, timestamp) VALUES (?, ?, ?)", (user.id, ctx.author.id, now))
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, ctx.author.id))
    bot.db.commit()
    await ctx.send(f"💍 Поздравляем! Вы теперь в браке с {user.mention}")

@bot.command(name="marriage_decline")
async def marriage_decline_cmd(ctx, user: discord.User):
    bot.cursor.execute("SELECT 1 FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, ctx.author.id))
    if not bot.cursor.fetchone():
        return await ctx.send("❌ У этого пользователя нет предложения для вас.")
    bot.cursor.execute("DELETE FROM marriage_proposals WHERE proposer_id = ? AND target_id = ?", (user.id, ctx.author.id))
    bot.db.commit()
    await ctx.send(f"❌ Вы отклонили предложение от {user.mention}")

@bot.command(name="marriage_divorce")
async def marriage_divorce_cmd(ctx, user: discord.User):
    bot.cursor.execute("SELECT 1 FROM marriages WHERE user_id = ? AND partner_id = ?", (ctx.author.id, user.id))
    if not bot.cursor.fetchone():
        return await ctx.send("❌ У вас нет брака с этим пользователем.")
    bot.cursor.execute("DELETE FROM marriages WHERE (user_id = ? AND partner_id = ?) OR (user_id = ? AND partner_id = ?)",
                       (ctx.author.id, user.id, user.id, ctx.author.id))
    bot.db.commit()
    await ctx.send(f"💔 Вы развелись с {user.mention}")

@bot.command(name="marriage_proposals")
async def marriage_proposals_cmd(ctx, page: int = 1):
    limit = 5
    offset = (page - 1) * limit
    bot.cursor.execute("SELECT proposer_id, timestamp FROM marriage_proposals WHERE target_id = ? LIMIT ? OFFSET ?", (ctx.author.id, limit, offset))
    proposals = bot.cursor.fetchall()
    if not proposals:
        return await ctx.send("📭 У вас нет предложений о браке.")
    embed = discord.Embed(title=f"💍 Предложения брака - страница {page}", color=0xF47FFF)
    for proposer_id, timestamp in proposals:
        proposer = ctx.guild.get_member(proposer_id)
        name = proposer.display_name if proposer else f"Unknown ({proposer_id})"
        dt = datetime.fromisoformat(timestamp)
        embed.add_field(name=name, value=f"Отправлено <t:{int(dt.timestamp())}:R>", inline=False)
    await ctx.send(embed=embed)

bot.run(os.getenv("DISCORD_TOKEN"))

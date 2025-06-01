import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_text(self, ctx):
        """Проверка задержки бота (Текстовая команда)"""
        await ctx.send(f'🏓 Pong! `{round(ctx.bot.latency * 1000)} ms`')

    @app_commands.command(name="ping", description="Проверка задержки бота")
    async def ping_slash(self, interaction: discord.Interaction):
        """Проверка задержки бота (Слэш-команда)"""
        await interaction.response.send_message(f'🏓 Pong! `{round(interaction.client.latency * 1000)} ms`')

    @commands.command(name="sync")
    async def sync_text(self, ctx):
        """Синхронизация слэш-команд (Текстовая команда)"""
        if ctx.author.guild_permissions.administrator:
            await ctx.bot.tree.sync()
            await ctx.send("✅ Все слэш-команды синхронизированы!")
        else:
            await ctx.send("❌ Только админ может синхронизировать команды.")

    @app_commands.command(name="sync", description="Синхронизация слэш-команд")
    async def sync_slash(self, interaction: discord.Interaction):
        """Синхронизация слэш-команд (Слэш-команда)"""
        if interaction.user.guild_permissions.administrator:
            await interaction.client.tree.sync()
            await interaction.response.send_message("✅ Все слэш-команды синхронизированы!")
        else:
            await interaction.response.send_message("❌ Только админ может синхронизировать команды!", ephemeral=True)

    @commands.command(name="prefix")
    async def prefix_text(self, ctx, new_prefix: str = None):
        """Изменение префикса команд (Текстовая команда)"""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Только админ может менять префикс.")

        if new_prefix:
            set_prefix(ctx.guild.id, new_prefix)
            await ctx.send(f"✅ Префикс изменён на `{new_prefix}`")
        else:
            await ctx.send(f"🔧 Текущий префикс: `{get_prefix(ctx.guild.id)}`")

    @app_commands.command(name="prefix", description="Изменить префикс команд")
    async def prefix_slash(self, interaction: discord.Interaction, new_prefix: str):
        """Изменение префикса команд (Слэш-команда)"""
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Только админ может менять префикс.", ephemeral=True)

        set_prefix(interaction.guild.id, new_prefix)
        await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

    @app_commands.command(name="setup", description="Настроить параметры верификации")
    async def setup_slash(self, interaction: discord.Interaction, role: discord.Role = None, username_format: str = None):
        """Настроить параметры верификации (Слэш-команда)"""
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Только админ может выполнять настройку.", ephemeral=True)

        execute_query(
            "INSERT INTO verification_settings (guild_id, role_id, username_format) VALUES (%s, %s, %s)"
            " ON DUPLICATE KEY UPDATE role_id=VALUES(role_id), username_format=VALUES(username_format)",
            (interaction.guild.id, role.id if role else None, username_format)
        )
        await interaction.response.send_message(f"✅ Настроено! Никнейм будет `{username_format}`.")

    @app_commands.command(name="help", description="Помощь по командам")
    async def help_slash(self, interaction: discord.Interaction):
        """Полный список команд"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value=(
            "`/prefix` - Изменить префикс команд\n"
            "`/sync` - Синхронизировать слэш-команды\n"
            "`/ping` - Проверить задержку\n"
            "`/setup [роль] [формат ника]` - Настроить параметры"
        ), inline=False)

        embed.add_field(name="💍 Брак", value=(
            "`/marriage info` - Информация про брак\n"
            "`/marriage list` - Просмотреть браки\n"
            "`/marriage marry <user>` - Сделать предложение\n"
            "`/marriage accept <user>` - Принять предложение\n"
            "`/marriage decline <user>` - Отклонить предложение\n"
            "`/marriage divorce <user>` - Развестись\n"
            "`/marriage proposals [page]` - Посмотреть предложения"
        ), inline=False)

        embed.add_field(name="🔍 Верификация", value=(
            "`/verify` - Получить ссылку для верификации\n"
            "`/setup [роль] [формат ника]` - Настроить параметры"
        ), inline=False)

        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Core(bot))

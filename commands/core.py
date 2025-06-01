import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping_text(self, ctx):
        """Проверка задержки бота (Текстовая версия)"""
        await ctx.send(f'🏓 Pong! `{round(self.bot.latency * 1000)} ms`')

    @app_commands.command(name="ping", description="Проверка задержки бота")
    async def ping_slash(self, interaction: discord.Interaction):
        """Проверка задержки бота (Слэш-команда)"""
        await interaction.response.send_message(f'🏓 Pong! `{round(self.bot.latency * 1000)} ms`')

    @commands.command(name="sync")
    async def sync_text(self, ctx):
        """Синхронизация слэш-команд (Текстовая версия)"""
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
        """Управление префиксом команд (Текстовая версия)"""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Только админ может менять префикс.")
        
        if new_prefix:
            set_prefix(ctx.guild.id, new_prefix)
            await ctx.send(f"✅ Префикс изменён на `{new_prefix}`")
        else:
            await ctx.send(f"🔧 Текущий префикс: `{get_prefix(ctx.guild.id)}`")

    @app_commands.command(name="prefix", description="Изменить префикс команд")
    async def prefix_slash(self, interaction: discord.Interaction, new_prefix: str):
        """Управление префиксом команд (Слэш-команда)"""
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Только админ может менять префикс.", ephemeral=True)

        set_prefix(interaction.guild.id, new_prefix)
        await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

    @commands.command(name="setup")
    async def setup_text(self, ctx, role: discord.Role = None, username_format: str = None):
        """Настроить параметры верификации (Текстовая версия)"""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Только админ может выполнять настройку.")

        execute_query(
            "INSERT INTO verification_settings (guild_id, role_id, username_format) VALUES (%s, %s, %s)"
            " ON DUPLICATE KEY UPDATE role_id=VALUES(role_id), username_format=VALUES(username_format)",
            (ctx.guild.id, role.id if role else None, username_format)
        )
        response = "✅ Настроено!"
        if role:
            response += f" Роль `{role.name}` будет выдаваться."
        if username_format:
            response += f" Никнейм будет по формату `{username_format}`."
        await ctx.send(response)

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
        response = "✅ Настроено!"
        if role:
            response += f" Роль `{role.name}` будет выдаваться."
        if username_format:
            response += f" Никнейм будет по формату `{username_format}`."
        await interaction.response.send_message(response)

async def setup(bot):
    await bot.add_cog(Core(bot))

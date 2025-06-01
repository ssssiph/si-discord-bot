import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="Проверка задержки бота")
    async def ping_slash(self, interaction: discord.Interaction):
        """Проверка задержки бота (Слэш-команда)"""
        await interaction.response.send_message(f'🏓 Pong! `{round(interaction.client.latency * 1000)} ms`')

    @app_commands.command(name="sync", description="Синхронизация слэш-команд")
    async def sync_slash(self, interaction: discord.Interaction):
        """Синхронизация слэш-команд (Слэш-команда)"""
        if interaction.user.guild_permissions.administrator:
            await interaction.client.tree.sync()
            await interaction.response.send_message("✅ Все слэш-команды синхронизированы!")
        else:
            await interaction.response.send_message("❌ Только админ может синхронизировать команды!", ephemeral=True)

    @app_commands.command(name="prefix", description="Изменить префикс команд")
    async def prefix_slash(self, interaction: discord.Interaction, new_prefix: str):
        """Изменение префикса команд"""
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Только админ может менять префикс.", ephemeral=True)

        set_prefix(interaction.guild.id, new_prefix)
        await interaction.response.send_message(f"✅ Префикс изменён на `{new_prefix}`")

    @app_commands.command(name="help", description="Помощь по командам")
    async def help_slash(self, interaction: discord.Interaction):
        """Помощь по командам (Слэш-команда)"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value="`/prefix` - Изменить префикс команд\n`/sync` - Синхронизировать слэш-команды\n`/ping` - Проверить задержку", inline=False)
        embed.add_field(name="💍 Брак", value="`/marriage list` - Просмотреть браки\n`/marriage marry <user>` - Сделать предложение\n`/marriage divorce <user>` - Развестись", inline=False)
        embed.add_field(name="🔍 Верификация", value="`/verify` - Получить ссылку для верификации\n`/setup [роль] [формат ника]` - Настроить параметры", inline=False)
        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Core(bot))

import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
        await ctx.send(f"✅ Настроено! Никнейм будет `{username_format}`.")

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
        """Помощь по командам (Слэш-команда)"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value="`/prefix` - Изменить префикс команд\n`/sync` - Синхронизировать слэш-команды", inline=False)
        embed.add_field(name="💍 Брак", value=(
            "`/marriage list` - Просмотреть свои браки\n"
            "`/marriage marry <member>` - Отправить предложение\n"
            "`/marriage accept <user>` - Принять предложение\n"
            "`/marriage decline <user>` - Отклонить предложение\n"
            "`/marriage divorce <user>` - Развестись\n"
            "`/marriage proposals [page]` - Посмотреть предложения"
        ), inline=False)
        embed.add_field(name="🔍 Верификация", value="`/verify` - Получить ссылку для верификации\n`/setup [роль] [формат ника]` - Настроить параметры", inline=False)
        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Core(bot))

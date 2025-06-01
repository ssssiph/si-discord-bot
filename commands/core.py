import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_text(self, ctx):
        """Помощь по командам (Текстовая версия)"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value="`!prefix` - Изменить префикс команд\n`!sync` - Синхронизировать слэш-команды", inline=False)
        embed.add_field(name="💍 Брак", value="`/marriage info` - Информация про брак\n`/marriage marry <member>` - Отправить предложение", inline=False)
        embed.add_field(name="🔍 Верификация", value="`/verify` - Получить ссылку для верификации\n`!setup [роль] [формат ника]` - Настроить параметры", inline=False)
        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="Помощь по командам")
    async def help_slash(self, interaction: discord.Interaction):
        """Помощь по командам (Слэш-команда)"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value="`/prefix` - Изменить префикс команд\n`/sync` - Синхронизировать слэш-команды", inline=False)
        embed.add_field(name="💍 Брак", value="`/marriage info` - Информация про брак\n`/marriage marry <member>` - Отправить предложение", inline=False)
        embed.add_field(name="🔍 Верификация", value="`/verify` - Получить ссылку для верификации\n`/setup [роль] [формат ника]` - Настроить параметры", inline=False)
        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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

async def setup(bot):
    await bot.add_cog(Core(bot))

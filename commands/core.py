import discord
from discord.ext import commands
from db.db import execute_query, get_prefix, set_prefix

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Проверка задержки бота"""
        await ctx.send(f'🏓 Pong! `{round(self.bot.latency * 1000)} ms`')

    @commands.command(name="prefix")
    async def prefix(self, ctx, new_prefix: str = None):
        """Управление префиксом команд"""
        if not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ Только админ может менять префикс.")
        
        if new_prefix:
            set_prefix(ctx.guild.id, new_prefix)
            await ctx.send(f"✅ Префикс изменён на `{new_prefix}`")
        else:
            await ctx.send(f"🔧 Текущий префикс: `{get_prefix(ctx.guild.id)}`")

    @commands.command(name="setup")
    async def setup(self, ctx, role: discord.Role = None, username_format: str = None):
        """Настроить параметры верификации"""
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

    @commands.command(name="help")
    async def help(self, ctx):
        """Список команд"""
        embed = discord.Embed(title="🤖 Помощь по командам", color=0x5865F2)

        embed.add_field(name="🛡️ Модерация", value="`/prefix` - Изменить префикс команд", inline=False)
        embed.add_field(name="💰 Экономика", value="Скоро!", inline=False)

        embed.add_field(name="💍 Брак", value=(
            "`/marriage info` - Информация про брак\n"
            "`/marriage marry <member>` - Отправить предложение о браке\n"
            "`/marriage accept <user>` - Принять предложение\n"
            "`/marriage decline <user>` - Отклонить предложение\n"
            "`/marriage divorce <user>` - Развестись\n"
            "`/marriage list` - Просмотреть свои браки\n"
            "`/marriage proposals [page]` - Посмотреть предложения"
        ), inline=False)

        embed.add_field(name="🔍 Верификация", value=(
            "`/verify` - Получить ссылку для верификации\n"
            "`/setup [роль] [формат ника]` - Настроить параметры"
        ), inline=False)

        embed.set_footer(text="Спасибо, что используете нашего бота 💙")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Core(bot))

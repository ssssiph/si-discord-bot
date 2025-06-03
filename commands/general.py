import discord
from discord.ext import commands
from set_prefix import set_prefix
from get_prefix import get_prefix

def setup(bot):
    """Регистрация текстовых команд"""

    @bot.command(name="ping", aliases=["пинг"])
    @commands.has_permissions(administrator=True)
    async def ping(ctx):
        """Проверяет задержку бота"""
        latency = round(bot.latency * 1000)
        await ctx.reply(f"🏓 Pong! Latency: {latency}ms")

    @bot.command(name="prefix", aliases=["префикс"])
    @commands.has_permissions(administrator=True)
    async def prefix(ctx, new_prefix: str = None):
        """Получает или изменяет префикс"""
        if new_prefix is None:
            current = get_prefix(ctx.guild.id)
            await ctx.reply(f"🔧 Текущий префикс: `{current}`")
        else:
            if len(new_prefix) > 10:
                await ctx.reply("❌ Префикс слишком длинный! Максимум 10 символов.")
                return
            set_prefix(ctx.guild.id, new_prefix)
            await ctx.reply(f"✅ Префикс изменён на: `{new_prefix}`")

    @bot.command(name="sync", aliases=["синк"])
    @commands.has_permissions(administrator=True)
    async def sync(ctx):
        """Синхронизирует слэш-команды"""
        await ctx.reply("📜 Синхронизирую слэш-команды...")
        try:
            await bot.tree.sync()
            await ctx.reply("✅ Слэш-команды синхронизированы!")
        except Exception as e:
            await ctx.reply(f"❌ Ошибка синхронизации: {e}")

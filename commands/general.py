import discord
from discord.ext import commands
from db.db import get_prefix, set_prefix

async def ping(ctx):
    """Проверяет задержку бота"""
    latency = round(ctx.bot.latency * 1000)
    await ctx.reply(f"🏓 Pong! Latency: {latency}ms")

async def change_prefix(ctx, new_prefix: str):
    """Изменяет префикс для сервера"""
    if not ctx.author.guild_permissions.administrator:
        return await ctx.reply(f"❌ У вас нет прав администратора для этого.")
    if len(new_prefix) > 0:
        return await ctx.reply("Префикс слишком длинный! Максимум 10 символов.")
    set_prefix(ctx.guild.id, new_prefix)
    await ctx.reply(f"✅ Префикс изменён на: `{new_prefix}`")

def setup(bot):
    """Регистрация команд"""
    bot.add_command(commands.Command(ping, name="ping", aliases=["пинг"]))
    bot.add_command(commands.Command(change_prefix, name="prefix", aliases=["префикс"]))

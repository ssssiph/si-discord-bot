import discord
from discord.ext import commands
from db import get_prefix, set_prefix

async def ping(ctx):
    latency = round(ctx.bot.latency * 1000)
    await ctx.send(f'🏓 Pong! `{latency} ms`')

async def change_prefix(ctx, new_prefix: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ У тебя нет прав администратора.")
        return

    set_prefix(ctx.guild.id, new_prefix)
    await ctx.send(f"✅ Префикс изменён на `{new_prefix}`")

def setup_commands(bot):
    @bot.command(name="ping", aliases=["пинг"])
    async def ping_command(ctx):
        await ping(ctx)

    @bot.command(name="prefix")
    async def prefix_command(ctx, new_prefix: str = None):
        if new_prefix is None:
            current = get_prefix(ctx.guild.id)
            await ctx.send(f"🔧 Текущий префикс: `{current}`")
        else:
            await change_prefix(ctx, new_prefix)

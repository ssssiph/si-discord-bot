import discord
from discord import app_commands
from discord.ext import commands
import requests
from db.db import execute_query
import os

VERIFY_LINK = os.getenv("VERIFY_URL")

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Пройти верификацию")
    async def verify(self, interaction: discord.Interaction):
        """Отправляет ссылку для верификации"""
        await interaction.response.send_message(
            f"🔍 Чтобы пройти верификацию, перейдите по [этой ссылке]({VERIFY_LINK}).", ephemeral=True
        )

    async def on_member_update(self, before, after):
        """Обработчик смены ролей и ника после верификации"""
        verified = execute_query("SELECT roblox_id, roblox_name, display_name, roblox_age, roblox_join_date FROM verifications WHERE discord_id = %s", 
                                 (after.id,), fetch_one=True)
        if verified:
            role_id = execute_query("SELECT role_id FROM verification_settings WHERE guild_id = %s", (after.guild.id,), fetch_one=True)
            if role_id:
                role = after.guild.get_role(role_id[0])
                if role and role not in after.roles:
                    await after.add_roles(role)

            # Меняем ник по указанному формату
            username_format = execute_query("SELECT username_format FROM verification_settings WHERE guild_id = %s", (after.guild.id,), fetch_one=True)
            if username_format:
                new_nickname = username_format[0].replace("{roblox-name}", verified[1]) \
                                                 .replace("{display-name}", verified[2]) \
                                                 .replace("{smart-name}", f"{verified[2]} (@{verified[1]})") \
                                                 .replace("{roblox-id}", str(verified[0])) \
                                                 .replace("{roblox-age}", str(verified[3])) \
                                                 .replace("{roblox-join-date}", verified[4])
                await after.edit(nick=new_nickname)

            welcome_message = f"🎉 **Добро пожаловать в {after.guild.name}, {new_nickname}!**"
            await after.guild.system_channel.send(welcome_message)

async def setup(bot):
    await bot.add_cog(Verification(bot))

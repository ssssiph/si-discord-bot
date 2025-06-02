import discord
from discord import app_commands
from discord.ext import commands
import os
from db.db import execute_query

VERIFY_LINK = os.getenv("VERIFY_URL", "https://siph-industry.com/verification")

class Verification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Пройти верификацию")
    async def verify(self, interaction: discord.Interaction):
        """Отправляет ссылку для верификации"""
        await interaction.response.send_message(
            f"🔍 Чтобы пройти верификацию, перейдите по [этой ссылке]({VERIFY_LINK}).", ephemeral=True
        )

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        """Обработчик смены ролей, ника и отправки приветственного сообщения"""
        verified = execute_query(
            "SELECT roblox_id, roblox_name, display_name, roblox_age, roblox_join_date FROM verifications WHERE discord_id = %s AND status = %s",
            (after.id, "verified"), fetch_one=True
        )

        if verified:
            role_id = execute_query("SELECT role_id FROM verification_settings WHERE guild_id = %s", (after.guild.id,), fetch_one=True)
            if role_id and role_id[0]:
                role = after.guild.get_role(role_id[0])
                if role and role not in after.roles:
                    try:
                        await after.add_roles(role)
                    except Exception as e:
                        print(f"Ошибка выдачи роли: {e}")

            username_format = execute_query("SELECT username_format FROM verification_settings WHERE guild_id = %s", (after.guild.id,), fetch_one=True)
            if username_format and username_format[0]:
                new_nickname = username_format[0].replace("{roblox-name}", verified[1]) \
                                                .replace("{display-name}", verified[2]) \
                                                .replace("{smart-name}", f"{verified[2]} (@{verified[1]})") \
                                                .replace("{roblox-id}", str(verified[0])) \
                                                .replace("{roblox-age}", str(verified[3])) \
                                                .replace("{roblox-join-date}", str(verified[4]))
                try:
                    await after.edit(nick=new_nickname[:32])  # Ограничение Discord
                except Exception as e:
                    print(f"Ошибка смены ника: {e}")

            if after.guild.system_channel:
                welcome_message = f"🎉 **Добро пожаловать в {after.guild.name}, {new_nickname[:32]}!**"
                try:
                    await after.guild.system_channel.send(welcome_message)
                except Exception as e:
                    print(f"Ошибка отправки приветствия: {e}")

async def setup(bot):
    await bot.add_cog(Verification(bot))

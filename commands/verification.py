import discord
from discord import app_commands
import requests
from db.db import execute_query

VERIFY_TEXT_URL = "https://users.roblox.com/v1/users/"

class Verification(commands.GroupCog, name="verification"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Начать верификацию")
    async def verify(self, interaction: discord.Interaction, roblox_username: str):
        await interaction.response.send_message(f"🔍 Проверяю пользователя `{roblox_username}`...", ephemeral=True)

        response = requests.get(f"{VERIFY_TEXT_URL}{roblox_username}")
        if response.status_code == 200:
            user_data = response.json()
            execute_query("INSERT INTO verifications (discord_id, roblox_id) VALUES (%s, %s)", (interaction.user.id, user_data["id"]))
            await interaction.followup.send(f"✅ Верификация `{roblox_username}` успешна!", ephemeral=True)
        else:
            await interaction.followup.send(f"❌ Не удалось проверить `{roblox_username}`, попробуйте позже.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Verification(bot))

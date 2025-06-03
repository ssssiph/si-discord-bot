import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query

class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setup", description="Настроить верификацию на сервере")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(self, interaction: discord.Interaction, role_id: str, username_format: str):
        guild_id = interaction.guild_id
        try:
            execute_query(
                "INSERT INTO verification_settings (guild_id, role_id, username_format) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE role_id = %s, username_format = %s",
                (guild_id, role_id, username_format, role_id, username_format)
            )
            await interaction.response.send_message("✅ Настройки верификации сохранены!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @app_commands.command(name="verify", description="Начать верификацию")
    async def verify(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            "Перейдите по ссылке для верификации: https://siph-industry.com/verification",
            ephemeral=True
        )

def setup(bot):
    print("Добавляю команды core...")
    bot.add_cog(Core(bot))
    print("Команды core добавлены!")

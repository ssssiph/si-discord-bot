import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query

def setup(bot):
    print("Добавляю команды core...")
    bot.tree.add_command(app_commands.Command(
        name="setup",
        description="Настроить верификацию на сервере",
        callback=setup_callback,
        default_permissions=discord.Permissions(administrator=True),
        guilds=[discord.Object(id=guild_id) for guild_id in bot.guilds]  # Ограничение по гильдиям (опционально)
    ))
    bot.tree.add_command(app_commands.Command(
        name="verify",
        description="Начать верификацию",
        callback=verify_callback,
        guilds=[discord.Object(id=guild_id) for guild_id in bot.guilds]  # Ограничение по гильдиям (опционально)
    ))
    print("Команды core добавлены!")

async def setup_callback(interaction: discord.Interaction, role_id: str, username_format: str):
    guild_id = interaction.guild_id
    try:
        execute_query(
            "INSERT INTO verification_settings (guild_id, role_id, username_format) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE role_id = %s, username_format = %s",
            (guild_id, role_id, username_format, role_id, username_format)
        )
        await interaction.response.send_message("✅ Настройки верификации сохранены!", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

async def verify_callback(interaction: discord.Interaction):
    await interaction.response.send_message(
        "Перейдите по ссылке для верификации: https://siph-industry.com/verification",
        ephemeral=True
    )

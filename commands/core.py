import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query

def setup(bot):
    """Регистрация слэш-команд"""

    @bot.tree.command(name="setup", description="Настройка верификации для сервера")
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_command(interaction: discord.Interaction, role_id: str, nickname_format: str = "{roblox-name}"):
        """Настраивает верификацию: роль и формат никнейма"""
        guild_id = interaction.guild_id
        valid_formats = ["{roblox-name}", "{display-name}", "{roblox-id}", "{discord-name}"]
        if not any(fmt in nickname_format for fmt in valid_formats):
            await interaction.response.send_message(
                "❌ Неверный формат никнейма! Используйте: `{roblox-name}`, `{display-name}`, `{roblox-id}`, `{discord-name}`\n"
                "Пример: `{roblox-name} | {discord-name}`",
                ephemeral=True
            )
            return

        try:
            role = interaction.guild.get_role(int(role_id))
            if not role:
                await interaction.response.send_message("❌ Роль не найдена!", ephemeral=True)
                return

            execute_query(
                "REPLACE INTO verification_settings (guild_id, role_id, username_format) VALUES (%s, %s, %s)",
                (guild_id, int(role_id), nickname_format)
            )
            await interaction.response.send_message(
                f"✅ Настройка завершена!\nРоль: {role.mention}\nФормат никнейма: `{nickname_format}`",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка настройки: {e}", ephemeral=True)

    @bot.tree.command(name="verify", description="Начать верификацию Roblox")
    async def verify_command(interaction: discord.Interaction):
        """Перенаправляет на страницу верификации"""
        await interaction.response.send_message(
            "🔗 Перейдите для верификации: https://siph-industry.com/verification",
            ephemeral=True
        )

    @bot.tree.command(name="unlink", description="Отвязать Roblox-аккаунт")
    async def unlink_command(interaction: discord.Interaction):
        """Удаляет верификацию пользователя"""
        discord_id = interaction.user.id
        try:
            result = execute_query(
                "DELETE FROM verifications WHERE discord_id = %s",
                (discord_id,),
                fetch_one=True
            )
            if result:
                await interaction.response.send_message("✅ Аккаунт отвязан!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Вы не верифицированы!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @bot.tree.command(name="whois", description="Информация о верифицированном пользователе")
    async def whois_command(interaction: discord.Interaction, user: discord.User):
        """Показывает данные верификации"""
        discord_id = user.id
        try:
            result = execute_query(
                "SELECT roblox_name, display_name, roblox_id, roblox_join_date FROM verifications WHERE discord_id = %s",
                (discord_id,),
                fetch_one=True
            )
            if result:
                roblox_name, display_name, roblox_id, join_date = result
                embed = discord.Embed(
                    title=f"Верификация {user.display_name}",
                    color=discord.Color.green()
                )
                embed.add_field(name="Roblox ник", value=roblox_name, inline=True)
                embed.add_field(name="Отображаемое имя", value=display_name, inline=True)
                embed.add_field(name="Roblox ID", value=roblox_id, inline=True)
                embed.add_field(name="Дата регистрации", value=join_date, inline=True)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Пользователь не верифицирован!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @bot.tree.command(name="setnickname", description="Установить формат никнейма для сервера")
    @app_commands.checks.has_permissions(administrator=True)
    async def setnickname_command(interaction: discord.Interaction, nickname_format: str):
        """Устанавливает формат никнейма для верифицированных пользователей"""
        guild_id = interaction.guild_id
        valid_formats = ["{roblox-name}", "{display-name}", "{roblox-id}", "{discord-name}"]
        if not any(fmt in nickname_format for fmt in valid_formats):
            await interaction.response.send_message(
                "❌ Неверный формат никнейма! Используйте: `{roblox-name}`, `{display-name}`, `{roblox-id}`, `{discord-name}`\n"
                "Пример: `{roblox-name} | {discord-name}`",
                ephemeral=True
            )
            return

        try:
            execute_query(
                "UPDATE verification_settings SET username_format = %s WHERE guild_id = %s",
                (nickname_format, guild_id)
            )
            await interaction.response.send_message(
                f"✅ Формат никнейма установлен: `{nickname_format}`",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query
import time

async def setup(bot):
    """Регистрация команд браков"""
    print("Добавляю команды marriage...")

    @bot.tree.command(name="propose", description="Предложить брак пользователю")
    async def propose_command(interaction: discord.Interaction, user: discord.User):
        """Отправляет предложение брака"""
        proposer_id = interaction.user.id
        target_id = user.id
        if proposer_id == target_id:
            await interaction.response.send_message("❌ Нельзя предложить брак себе!", ephemeral=True)
            return

        # Проверка текущих браков
        marriages = execute_query(
            "SELECT partner_id FROM marriages WHERE user_id = %s",
            (proposer_id,),
            fetch_all=True
        )
        limit = execute_query(
            "SELECT marriage_limit FROM marriage_limits WHERE user_id = %s",
            (proposer_id,),
            fetch_one=True
        )
        limit = limit[0] if limit else 1
        if len(marriages) >= limit:
            await interaction.response.send_message("❌ Вы достигли лимита браков!", ephemeral=True)
            return

        # Проверка существующих предложений
        proposal = execute_query(
            "SELECT timestamp FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
            (proposer_id, target_id),
            fetch_one=True
        )
        if proposal:
            await interaction.response.send_message("❌ Вы уже отправили предложение этому пользователю!", ephemeral=True)
            return

        try:
            execute_query(
                "INSERT INTO marriage_proposals (proposer_id, target_id, timestamp) VALUES (%s, %s, %s)",
                (proposer_id, target_id, time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            await interaction.response.send_message(
                f"💍 {interaction.user.mention} предложил брак {user.mention}! Ответьте с помощью `/accept` или `/decline`.",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @bot.tree.command(name="accept", description="Принять предложение брака")
    async def accept_command(interaction: discord.Interaction, user: discord.User):
        """Принимает предложение брака"""
        target_id = interaction.user.id
        proposer_id = user.id

        proposal = execute_query(
            "SELECT timestamp FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
            (proposer_id, target_id),
            fetch_one=True
        )
        if not proposal:
            await interaction.response.send_message("❌ Нет активного предложения от этого пользователя!", ephemeral=True)
            return

        try:
            execute_query(
                "INSERT INTO marriages (user_id, partner_id, timestamp) VALUES (%s, %s, %s), (%s, %s, %s)",
                (proposer_id, target_id, time.strftime("%Y-%m-%d %H:%M:%S"), target_id, proposer_id, time.strftime("%Y-%m-%d %H:%M:%S"))
            )
            execute_query(
                "DELETE FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                (proposer_id, target_id)
            )
            await interaction.response.send_message(
                f"🎉 {interaction.user.mention} и {user.mention} теперь в браке!",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @bot.tree.command(name="decline", description="Отклонить предложение брака")
    async def decline_command(interaction: discord.Interaction, user: discord.User):
        """Отклоняет предложение брака"""
        target_id = interaction.user.id
        proposer_id = user.id

        proposal = execute_query(
            "SELECT timestamp FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
            (proposer_id, target_id),
            fetch_one=True
        )
        if not proposal:
            await interaction.response.send_message("❌ Нет активного предложения от этого пользователя!", ephemeral=True)
            return

        try:
            execute_query(
                "DELETE FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                (proposer_id, target_id)
            )
            await interaction.response.send_message(
                f"💔 {interaction.user.mention} отклонил предложение от {user.mention}.",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @bot.tree.command(name="divorce", description="Развестись с партнёром")
    async def divorce_command(interaction: discord.Interaction, user: discord.User):
        """Разводит пользователей"""
        user_id = interaction.user.id
        partner_id = user.id

        marriage = execute_query(
            "SELECT timestamp FROM marriages WHERE user_id = %s AND partner_id = %s",
            (user_id, partner_id),
            fetch_one=True
        )
        if not marriage:
            await interaction.response.send_message("❌ Вы не в браке с этим пользователем!", ephemeral=True)
            return

        try:
            execute_query(
                "DELETE FROM marriages WHERE (user_id = %s AND partner_id = %s) OR (user_id = %s AND partner_id = %s)",
                (user_id, partner_id, partner_id, user_id)
            )
            await interaction.response.send_message(
                f"💔 {interaction.user.mention} и {user.mention} развелись.",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    print("Команды marriage добавлены!")

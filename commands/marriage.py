import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query
import time

async def setup(bot):
    """Регистрация команд браков"""
    print("Добавляю команды marriage...")

    marriage_group = app_commands.Group(name="marriage", description="Команды для управления браками")

    @marriage_group.command(name="info", description="Информация про брак")
    async def marriage_info(interaction: discord.Interaction):
        """Показывает информацию о текущем браке пользователя"""
        user_id = interaction.user.id
        marriage = execute_query(
            "SELECT partner_id, timestamp FROM marriages WHERE user_id = %s",
            (user_id,),
            fetch_one=True
        )
        if not marriage:
            await interaction.response.send_message("❌ Вы не состоите в браке!", ephemeral=True)
            return
        partner_id = marriage["partner_id"]
        timestamp = marriage["timestamp"]
        partner = await bot.fetch_user(partner_id)
        embed = discord.Embed(
            title="💍 Информация о браке",
            description=f"Вы в браке с {partner.mention} с {timestamp.strftime('%Y-%m-%d %H:%M:%S')}.",
            color=0xCCB4E4
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @marriage_group.command(name="list", description="Просмотреть браки")
    async def marriage_list(interaction: discord.Interaction):
        """Показывает список всех браков пользователя"""
        user_id = interaction.user.id
        marriages = execute_query(
            "SELECT partner_id, timestamp FROM marriages WHERE user_id = %s",
            (user_id,),
            fetch_all=True
        )
        if not marriages:
            await interaction.response.send_message("❌ У вас нет браков!", ephemeral=True)
            return
        embed = discord.Embed(title="💞 Ваши браки", color=0xCCB4E4)
        for marriage in marriages:
            partner_id = marriage["partner_id"]
            partner = await bot.fetch_user(partner_id)
            embed.add_field(
                name=f"Партнёр: {partner.name}",
                value=f"Дата: {marriage['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @marriage_group.command(name="marry", description="Сделать предложение")
    async def marriage_marry(interaction: discord.Interaction, user: discord.User):
        """Отправляет предложение брака"""
        proposer_id = interaction.user.id
        target_id = user.id
        if proposer_id == target_id:
            await interaction.response.send_message("❌ Нельзя предложить брак себе!", ephemeral=True)
            return
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
                f"💍 {interaction.user.mention} предложил брак {user.mention}! Ответьте с помощью `/marriage accept` или `/marriage decline`.",
                ephemeral=False
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Ошибка: {e}", ephemeral=True)

    @marriage_group.command(name="accept", description="Принять предложение")
    async def marriage_accept(interaction: discord.Interaction, user: discord.User):
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

    @marriage_group.command(name="decline", description="Отклонить предложение")
    async def marriage_decline(interaction: discord.Interaction, user: discord.User):
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

    @marriage_group.command(name="divorce", description="Развестись")
    async def marriage_divorce(interaction: discord.Interaction, user: discord.User):
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

    @marriage_group.command(name="proposals", description="Посмотреть предложения")
    async def marriage_proposals(interaction: discord.Interaction, page: int = 1):
        """Показывает список полученных предложений (по страницам)"""
        user_id = interaction.user.id
        per_page = 5
        offset = (page - 1) * per_page
        proposals = execute_query(
            "SELECT proposer_id, timestamp FROM marriage_proposals WHERE target_id = %s LIMIT %s OFFSET %s",
            (user_id, per_page, offset),
            fetch_all=True
        )
        if not proposals:
            await interaction.response.send_message("❌ У вас нет предложений!", ephemeral=True)
            return
        embed = discord.Embed(title="💌 Ваши предложения", color=0xCCB4E4)
        for proposal in proposals:
            proposer_id = proposal["proposer_id"]
            proposer = await bot.fetch_user(proposer_id)
            embed.add_field(
                name=f"От: {proposer.name}",
                value=f"Дата: {proposal['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
                inline=False
            )
        total_proposals = execute_query(
            "SELECT COUNT(*) FROM marriage_proposals WHERE target_id = %s",
            (user_id,),
            fetch_one=True
        )[0]
        total_pages = (total_proposals + per_page - 1) // per_page
        embed.set_footer(text=f"Страница {page}/{total_pages}")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    bot.tree.add_command(marriage_group)
    print("Команды marriage успешно добавлены!")

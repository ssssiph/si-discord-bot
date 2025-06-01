import discord
from discord import app_commands
from discord.ext import commands
from db.db import execute_query
from datetime import datetime

class Marriage(commands.GroupCog, name="marriage"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="info", description="Информация о браке")
    async def marriage_info(self, interaction: discord.Interaction):
        """Информация о механике брака"""
        embed = discord.Embed(title="💍 Информация о браке", color=0xF47FFF)
        embed.description = (
            "Брак — это связь между двумя пользователями, позволяющая им использовать специальные команды.\n"
            "Вы можете предлагать брак, принимать или отклонять предложения, разводиться и просматривать список своих партнёров."
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="list", description="Просмотреть список браков")
    async def marriage_list(self, interaction: discord.Interaction):
        """Вывести список текущих браков"""
        marriages = execute_query("SELECT partner_id, timestamp FROM marriages WHERE user_id = %s", 
                                  (interaction.user.id,), fetch_all=True)
        if not marriages:
            return await interaction.response.send_message("💔 У вас нет браков.")

        embed = discord.Embed(title="💍 Ваши браки", color=0xF47FFF)
        for partner_id, timestamp in marriages:
            partner = interaction.guild.get_member(partner_id)
            name = partner.display_name if partner else f"Unknown ({partner_id})"
            dt = datetime.fromisoformat(timestamp)
            embed.add_field(name=name, value=f"В браке с <t:{int(dt.timestamp())}:R>", inline=False)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="marry", description="Предложить пользователю вступить в брак")
    async def marriage_marry(self, interaction: discord.Interaction, member: discord.Member):
        """Отправить предложение о браке"""
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ Нельзя жениться на себе.", ephemeral=True)

        limit_count = execute_query("SELECT limit_count FROM marriage_limits WHERE user_id = %s", 
                                    (interaction.user.id,), fetch_one=True)

        if limit_count is None:
            execute_query("INSERT INTO marriage_limits (user_id, limit_count) VALUES (%s, %s)", 
                          (interaction.user.id, 1))
            limit_count = (1,)

        current_marriages = execute_query("SELECT COUNT(*) FROM marriages WHERE user_id = %s", 
                                          (interaction.user.id,), fetch_one=True)[0]

        current_requests = execute_query("SELECT COUNT(*) FROM marriage_proposals WHERE proposer_id = %s",
                                         (interaction.user.id,), fetch_one=True)[0]

        if (current_marriages + current_requests) >= limit_count[0]:
            return await interaction.response.send_message("❌ Вы уже достигли лимита браков и запросов.", ephemeral=True)

        execute_query("INSERT INTO marriage_proposals (proposer_id, target_id, timestamp) VALUES (%s, %s, %s)",
                      (interaction.user.id, member.id, datetime.utcnow().isoformat()))

        embed = discord.Embed(title="💍 Предложение!", color=0xF47FFF)
        embed.add_field(name="Кто предлагает", value=interaction.user.mention)
        embed.add_field(name="Кому", value=member.mention)
        embed.set_footer(text="Используйте /marriage accept, чтобы принять.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="accept", description="Принять предложение о браке")
    async def marriage_accept(self, interaction: discord.Interaction, user: discord.User):
        """Принять предложение о браке"""
        proposal = execute_query("SELECT timestamp FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                                 (user.id, interaction.user.id), fetch_one=True)
        if not proposal:
            return await interaction.response.send_message("❌ У этого пользователя нет предложения для вас.", ephemeral=True)

        execute_query("DELETE FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                      (user.id, interaction.user.id))

        now = datetime.utcnow().isoformat()
        execute_query("INSERT INTO marriages (user_id, partner_id, timestamp) VALUES (%s, %s, %s)", 
                      (interaction.user.id, user.id, now))
        execute_query("INSERT INTO marriages (user_id, partner_id, timestamp) VALUES (%s, %s, %s)", 
                      (user.id, interaction.user.id, now))

        await interaction.response.send_message(f"💍 Поздравляем! Вы теперь в браке с {user.mention}")

    @app_commands.command(name="decline", description="Отклонить предложение о браке")
    async def marriage_decline(self, interaction: discord.Interaction, user: discord.User):
        """Отклонить предложение о браке"""
        proposal = execute_query("SELECT 1 FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                                 (user.id, interaction.user.id), fetch_one=True)
        if not proposal:
            return await interaction.response.send_message("❌ У вас нет предложения от этого пользователя.", ephemeral=True)

        execute_query("DELETE FROM marriage_proposals WHERE proposer_id = %s AND target_id = %s",
                      (user.id, interaction.user.id))
        await interaction.response.send_message("✅ Предложение отклонено.")

    @app_commands.command(name="divorce", description="Развестись с пользователем")
    async def marriage_divorce(self, interaction: discord.Interaction, user: discord.User):
        """Оформить развод"""
        marriage = execute_query("SELECT 1 FROM marriages WHERE user_id = %s AND partner_id = %s",
                                 (interaction.user.id, user.id), fetch_one=True)
        if not marriage:
            return await interaction.response.send_message("❌ Вы не состоите в браке с этим пользователем.", ephemeral=True)

        execute_query("DELETE FROM marriages WHERE user_id = %s AND partner_id = %s", (interaction.user.id, user.id))
        execute_query("DELETE FROM marriages WHERE user_id = %s AND partner_id = %s", (user.id, interaction.user.id))

        embed = discord.Embed(title="💔 Развод оформлен", description=f"Вы больше не состоите в браке с {user.mention}.", color=0xFF0000)
        embed.set_footer(text="Вы всегда можете начать новую жизнь! 💡")
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Marriage(bot))

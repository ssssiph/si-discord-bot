import discord
from discord import app_commands
from discord.ext import commands

async def setup(bot):
    """Регистрация основных команд"""
    print("Добавляю команды core...")

    @bot.tree.command(name="help", description="Показать список доступных команд")
    async def help_command(interaction: discord.Interaction):
        """Показывает список всех доступных команд"""
        embed = discord.Embed(title="📖 Список команд", color=0xCCB4E4)
        embed.add_field(
            name="Верификация",
            value="`/verify` - Начать процесс верификации\n",
            inline=False
        )
        embed.add_field(
            name="Браки",
            value="`/marriage info` - Информация про брак\n"
                  "`/marriage list` - Просмотреть браки\n"
                  "`/marriage marry <user>` - Сделать предложение\n"
                  "`/marriage accept <user>` - Принять предложение\n"
                  "`/marriage decline <user>` - Отклонить предложение\n"
                  "`/marriage divorce <user>` - Развестись\n"
                  "`/marriage proposals [page]` - Посмотреть предложения",
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @bot.tree.command(name="verify", description="Начать процесс верификации")
    async def verify_command(interaction: discord.Interaction):
        """Перенаправляет на страницу верификации"""
        await interaction.response.send_message("Перейдите для верификации: https://siph-industry.com/verification", ephemeral=True)

    print("Команды core успешно добавлены!")

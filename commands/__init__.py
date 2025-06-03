from .core import setup as core_setup
from .general import setup as general_setup

async def setup(bot):
    try:
        print("Загружаю core...")
        await core_setup(bot)
        print("Загружаю general...")
        await general_setup(bot)
        print("Все расширения загружены!")
    except Exception as e:
        print(f"Ошибка в setup: {e}")
        raise

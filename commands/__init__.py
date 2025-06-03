from .core import setup as core_setup
from .marriage import setup as marriage_setup

async def setup(bot):
    try:
        print("Загружаю core...")
        await core_setup(bot)
        print("Загружаю marriage...")
        await marriage_setup(bot)
        print("Все расширения загружены!")
    except Exception as e:
        print(f"Ошибка в setup: {e}")
        raise

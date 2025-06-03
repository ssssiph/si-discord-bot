from .core import setup as core_setup

async def setup(bot):
    try:
        print("Загружаю core...")
        await core_setup(bot)
        print("Все расширения загружены!")
    except Exception as e:
        print(f"Ошибка в setup: {e}")
        raise

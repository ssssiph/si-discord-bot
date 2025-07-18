from db.db import execute_query

def get_prefix(guild_id):
    """Получение префикса для сервера"""
    result = execute_query("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,), fetch_one=True)
    return result[0] if result else "s!"

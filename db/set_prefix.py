from db.db import execute_query

def set_prefix(guild_id, prefix):
    """Изменение префикса для сервера"""
    execute_query("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (guild_id, prefix))

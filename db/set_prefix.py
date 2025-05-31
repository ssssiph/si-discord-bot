from db import execute_query

def set_prefix_db(guild_id, prefix):
    execute_query("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (guild_id, prefix))

from db import execute_query

def get_prefix_db(guild_id):
    result = execute_query("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,), fetch_one=True)
    return result[0] if result else "s!"

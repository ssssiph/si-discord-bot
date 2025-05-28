import mysql.connector
import os

def get_prefix_db(guild_id):
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )
    cursor = db.cursor()
    cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    db.close()
    return result[0] if result else "s!"

import mysql.connector
import os

def set_prefix_db(guild_id, prefix):
    db = mysql.connector.connect(
        host=os.getenv("MYSQL_HOST"),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
    )
    cursor = db.cursor()
    cursor.execute(
        "REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)",
        (guild_id, prefix)
    )
    db.commit()
    db.close()

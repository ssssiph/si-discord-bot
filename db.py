import os
import mysql.connector
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    url = urlparse(os.getenv("DATABASE_URL"))
    return mysql.connector.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        port=url.port or 3306
    )

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixes (
            guild_id BIGINT PRIMARY KEY,
            prefix VARCHAR(10) NOT NULL
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def get_prefix(guild_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row[0] if row else "s!"

def set_prefix(guild_id, prefix):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO prefixes (guild_id, prefix)
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE prefix = VALUES(prefix)
    """, (guild_id, prefix))
    conn.commit()
    cursor.close()
    conn.close()

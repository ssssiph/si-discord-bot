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

    # Таблица префиксов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prefixes (
            guild_id BIGINT PRIMARY KEY,
            prefix VARCHAR(10) NOT NULL
        )
    """)

    # Таблица браков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriages (
            user_id BIGINT,
            partner_id BIGINT,
            timestamp TEXT,
            PRIMARY KEY(user_id, partner_id)
        )
    """)

    # Таблица лимитов браков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriage_limits (
            user_id BIGINT PRIMARY KEY,
            marriage_limit INT DEFAULT 1
        )
    """)

    # Таблица предложений браков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS marriage_proposals (
            proposer_id BIGINT,
            target_id BIGINT,
            timestamp TEXT,
            PRIMARY KEY(proposer_id, target_id)
        )
    """)

    # Таблица верификации Roblox
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verifications (
            discord_id BIGINT PRIMARY KEY,
            roblox_id BIGINT UNIQUE NOT NULL,
            status TEXT DEFAULT 'pending'
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)
    result = None
    if fetch_one:
        result = cursor.fetchone()
    elif fetch_all:
        result = cursor.fetchall()
    conn.commit()
    cursor.close()
    conn.close()
    return result

def get_prefix(guild_id):
    result = execute_query("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,), fetch_one=True)
    return result[0] if result else "s!"

def set_prefix(guild_id, prefix):
    execute_query("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (guild_id, prefix))

import os
import mysql.connector
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    """Создание соединения с базой данных"""
    url = urlparse(os.getenv("DATABASE_URL"))
    return mysql.connector.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        port=url.port or 3306
    )

def init_db():
    """Автоматическое создание всех нужных таблиц"""
    conn = get_db_connection()
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
            roblox_name VARCHAR(255) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            roblox_age INT NOT NULL,
            roblox_join_date DATE NOT NULL,
            status TEXT NOT NULL
        )
    """)

    # Таблица настроек верификации
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verification_settings (
            guild_id BIGINT PRIMARY KEY,
            role_id BIGINT DEFAULT NULL,
            username_format VARCHAR(255) DEFAULT '{roblox-name}'
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

def execute_query(query, params=(), fetch_one=False, fetch_all=False):
    """Универсальное выполнение SQL-запросов"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = None
        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        conn.commit()
    except Exception as e:
        print(f"Ошибка базы данных: {e}")
        raise
    finally:
        cursor.close()
        conn.close()
    return result

def get_prefix(guild_id):
    """Получение префикса для сервера"""
    result = execute_query("SELECT prefix FROM prefixes WHERE guild_id = %s", (guild_id,), fetch_one=True)
    return result[0] if result else "s!"

def set_prefix(guild_id, prefix):
    """Изменение префикса для сервера"""
    execute_query("REPLACE INTO prefixes (guild_id, prefix) VALUES (%s, %s)", (guild_id, prefix))

init_db()

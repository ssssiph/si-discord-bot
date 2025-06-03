import os
import requests
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import urlparse
from dotenv import load_dotenv

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "https://siph-industry.com"}})  # Ограничиваем CORS
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

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_API_BASE = "https://discord.com/api/v10"

def get_verification_settings(guild_id):
    """Получает role_id и username_format из базы"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT role_id, username_format FROM verification_settings WHERE guild_id = %s", (guild_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def update_discord_profile(guild_id, discord_id, roblox_username):
    """Выдаёт роль и меняет никнейм в Discord"""
    settings = get_verification_settings(guild_id)
    if not settings:
        return False

    role_id, username_format = settings
    if not role_id or not username_format:
        return False

    new_nickname = username_format.replace("{roblox-name}", roblox_username)

    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    role_url = f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{discord_id}/roles/{role_id}"
    nickname_url = f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{discord_id}"

    response = requests.put(role_url, headers=headers)
    if not response.ok:
        print(f"Ошибка выдачи роли: {response.status_code} {response.text}")
        return False

    response = requests.patch(nickname_url, headers=headers, json={"nick": new_nickname[:32]})
    if not response.ok:
        print(f"Ошибка смены ника: {response.status_code} {response.text}")
        return False

    return True

@app.route("/proxy/roblox/users", methods=["POST"])
def proxy_roblox_users():
    """Прокси для Roblox API: поиск пользователя по нику"""
    try:
        response = requests.post(
            "https://users.roblox.com/v1/usernames/users",
            json=request.json,
            headers={"Content-Type": "application/json"}
        )
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/proxy/roblox/user/<user_id>", methods=["GET"])
def proxy_roblox_user(user_id):
    """Прокси для Roblox API: получение профиля пользователя"""
    try:
        response = requests.get(f"https://users.roblox.com/v1/users/{user_id}")
        return jsonify(response.json()), response.status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/verify/complete", methods=["POST"])
def verify_complete():
    """Сохранение верификации в базе и обновление профиля Discord"""
    data = request.json
    discord_id = data.get("discord_id")
    roblox_id = data.get("roblox_id")
    roblox_name = data.get("roblox_name")
    display_name = data.get("display_name")
    roblox_age = data.get("roblox_age")
    roblox_join_date = data.get("roblox_join_date")
    guild_id = data.get("guild_id")
    status = data.get("status", "verified")

    if not all([discord_id, roblox_id, roblox_name, display_name, roblox_age, roblox_join_date, guild_id]):
        return jsonify({"success": False, "error": "Недостаточно данных"}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO verifications (discord_id, roblox_id, roblox_name, display_name, roblox_age, roblox_join_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                roblox_id = VALUES(roblox_id),
                roblox_name = VALUES(roblox_name),
                display_name = VALUES(display_name),
                roblox_age = VALUES(roblox_age),
                roblox_join_date = VALUES(roblox_join_date),
                status = VALUES(status)
        """, (discord_id, roblox_id, roblox_name, display_name, roblox_age, roblox_join_date, status))
        conn.commit()
        cursor.close()
        conn.close()

        if update_discord_profile(guild_id, discord_id, roblox_name):
            return jsonify({"success": True, "message": "Верификация успешна"}), 200
        else:
            return jsonify({"success": False, "error": "Ошибка обновления профиля Discord"}), 500

    except Exception as e:
        print(f"Ошибка верификации: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

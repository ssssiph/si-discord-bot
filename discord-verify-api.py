import os
import json
import requests
import mysql.connector
from flask import Flask, request, jsonify

app = Flask(__name__)

db_config = os.getenv("DATABASE_URL")
conn = mysql.connector.connect(host=db_config, user="root", password="password", database="verification_db")
cursor = conn.cursor()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_API_BASE = "https://discord.com/api/v10"

def get_verification_settings(guild_id):
    """ Получает `role_id` и `username_format` из MySQL """
    cursor.execute("SELECT role_id, username_format FROM verification_settings WHERE guild_id = %s", (guild_id,))
    return cursor.fetchone()

def update_discord_profile(guild_id, discord_id, roblox_username):
    """ Выдаёт роль и меняет никнейм в Discord """
    role_id, username_format = get_verification_settings(guild_id)

    new_nickname = username_format.replace("{username}", roblox_username)

    headers = {"Authorization": f"Bot {DISCORD_TOKEN}", "Content-Type": "application/json"}
    role_url = f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{discord_id}/roles/{role_id}"
    nickname_url = f"{DISCORD_API_BASE}/guilds/{guild_id}/members/{discord_id}"

    requests.put(role_url, headers=headers)

    requests.patch(nickname_url, headers=headers, json={"nick": new_nickname})

@app.route("/api/discord-verify", methods=["POST"])
def verify_user():
    data = request.json
    discord_id = data.get("discord_id")
    roblox_id = data.get("roblox_id")
    guild_id = data.get("guild_id")

    if not discord_id or not roblox_id or not guild_id:
        return jsonify({"success": False, "error": "Недостаточно данных"}), 400

    cursor.execute("SELECT display_name FROM verifications WHERE roblox_id = %s", (roblox_id,))
    result = cursor.fetchone()

    if not result:
        return jsonify({"success": False, "error": "Пользователь не найден"}), 404

    display_name = result[0]

    update_discord_profile(guild_id, discord_id, display_name)

    return jsonify({"success": True, "message": "Верификация успешна"}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

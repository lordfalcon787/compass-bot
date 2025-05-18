from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
from oauth import Oauth
from utils.mongo_connection import MongoConnection
from functools import wraps
import requests

app = Flask(__name__)
app.config["SECRET_KEY"] = "1264646464646464646"

DEFAULT_CONFIG = {
    "moderation": {
        "warn": [],
        "timeout": [],
        "kick": [],
        "ban": [],
        "logs": None
    },
    "payout": {
        "channel": None,
        "claim": None,
        "queue": None,
        "role": None
    },
    "auto_responder": {
        "link_allowed": [],
        "words_allowed": [],
        "allowed": []
    }
}

try:
    mongo = MongoConnection.get_instance()
    db = mongo.get_db()
    configuration = db["Configuration"]
except Exception as e:
    print(f"Warning: MongoDB connection failed: {e}")
    configuration = None

BOT_CLIENT_ID = "1291996619490984037"
BOT_TOKEN = os.getenv("BOT_TOKEN")

@app.context_processor
def inject_user():
    authorized = 'user_logged_in_compass_dashboard' in session
    return {
        'authorized': authorized,
        'user': {
            'name': session.get('user_logged_in_compass_dashboard'),
            'avatar': session.get('user_avatar')
        } if authorized else None
    }

def check_bot_in_guild(guild_id, access_token):
    try:
        response = requests.get(
            f"https://discord.com/api/v10/guilds/{guild_id}/members/{BOT_CLIENT_ID}",
            headers={"Authorization": f"Bot {BOT_TOKEN}"}
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking bot presence: {e}")
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_logged_in_compass_dashboard'):
            print("Unauthorized")
            return redirect(url_for("index"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    authorized = 'user_logged_in_compass_dashboard' in session
    return render_template("index.html", 
                         discord_url=Oauth.discord_login_url,
                         authorized=authorized,
                         user={
                             'name': session.get('user_logged_in_compass_dashboard'),
                             'avatar': session.get('user_avatar')
                         } if authorized else None,
                         no_gradient=True)

@app.route("/login")
def login():
    code = request.args.get('code')
    at = Oauth.get_access_token(code)
    user = Oauth.get_user_json(at)
    guilds = user["guilds"]
    admin_guilds = []
    for guild in guilds:
        if (guild.get("permissions", 0) & 0x8) == 0x8:
            admin_guilds.append(guild)
    
    session.permanent = True
    session['user_logged_in_compass_dashboard'] = user.get("username")
    session['user_avatar'] = f"https://cdn.discordapp.com/avatars/{user.get('id')}/{user.get('avatar')}.png"
    session['access_token'] = at
    session['admin_guilds'] = admin_guilds
    return redirect(url_for("dashboard"))

@app.route("/dashboard")
@login_required
def dashboard():
    guilds = session['admin_guilds']
    for guild in guilds:
        guild['bot_present'] = check_bot_in_guild(guild['id'], session['access_token'])
    
    return render_template("dashboard.html", 
                         user={
                             'name': session.get('user_logged_in_compass_dashboard'),
                             'avatar': session.get('user_avatar')
                         },
                         guilds=guilds,
                         client_id=BOT_CLIENT_ID,
                         no_gradient=True)

@app.route("/server/<guild_id>/settings")
@login_required
def server_settings(guild_id):
    # Redirect to the v2 settings page
    return redirect(url_for("server_settings_v2", guild_id=guild_id))

@app.route("/server/<guild_id>/settings/v2")
@login_required
def server_settings_v2(guild_id):
    current_server = next((guild for guild in session['admin_guilds'] if guild['id'] == guild_id), None)
    if not current_server:
        return redirect(url_for("dashboard"))
    
    if not check_bot_in_guild(guild_id, session['access_token']):
        return redirect(url_for("dashboard"))
    
    config_data = get_guild_config(guild_id)
    
    return render_template("server_settings_v2.html",
                         current_server=current_server,
                         user={
                             'name': session.get('user_logged_in_compass_dashboard'),
                             'avatar': session.get('user_avatar')
                         },
                         server_config=config_data,
                         no_gradient=True)

@app.route("/api/guild/<server_id>/config", methods=['GET'])
@login_required
def get_guild_config(server_id):
    try:
        if configuration is not None:
            config = configuration.find_one({"_id": "config"})
            if config:
                guild_config = {}
                for setting_type, guild_settings in config.items():
                    if setting_type != "_id":
                        if setting_type == "moderation":
                            guild_config[setting_type] = {}
                            for action in ["warn", "timeout", "kick", "ban", "logs"]:
                                if action in guild_settings and server_id in guild_settings[action]:
                                    value = guild_settings[action][server_id]
                                    if isinstance(value, (list, tuple)):
                                        guild_config[setting_type][action] = [str(x) for x in value]
                                    else:
                                        guild_config[setting_type][action] = str(value)
                                elif action in DEFAULT_CONFIG.get("moderation", {}):
                                    value = DEFAULT_CONFIG["moderation"][action]
                                    if isinstance(value, (list, tuple)):
                                        guild_config[setting_type][action] = [str(x) for x in value]
                                    else:
                                        guild_config[setting_type][action] = str(value)
                        elif setting_type == "perks":
                            guild_config[setting_type] = {}
                            if "snipe" in guild_settings and server_id in guild_settings["snipe"]:
                                value = guild_settings["snipe"][server_id]
                                if isinstance(value, (list, tuple)):
                                    guild_config[setting_type]["snipe"] = [str(x) for x in value]
                                else:
                                    guild_config[setting_type]["snipe"] = str(value)
                            elif "snipe" in DEFAULT_CONFIG.get("perks", {}):
                                value = DEFAULT_CONFIG["perks"]["snipe"]
                                if isinstance(value, (list, tuple)):
                                    guild_config[setting_type]["snipe"] = [str(x) for x in value]
                                else:
                                    guild_config[setting_type]["snipe"] = str(value)
                        else:
                            if server_id in guild_settings:
                                value = guild_settings[server_id]
                                if isinstance(value, (list, tuple)):
                                    guild_config[setting_type] = [str(x) for x in value]
                                else:
                                    guild_config[setting_type] = str(value)
                            elif setting_type in DEFAULT_CONFIG:
                                value = DEFAULT_CONFIG[setting_type]
                                if isinstance(value, (list, tuple)):
                                    guild_config[setting_type] = [str(x) for x in value]
                                else:
                                    guild_config[setting_type] = str(value)
                print(guild_config)
                return guild_config
        return jsonify(DEFAULT_CONFIG)
    except Exception as e:
        print(f"Error getting config: {e}")
        return jsonify(DEFAULT_CONFIG)

@app.route("/api/guild/<server_id>/config", methods=['POST'])
@login_required
def save_guild_config(server_id):
    try:
        if configuration is not None:
            print("Saving config")
            config_data = request.json
            
            current_config = configuration.find_one({"_id": "config"}) or {}
            
            for setting_type, settings in config_data.items():
                if setting_type == "moderation":
                    if setting_type not in current_config:
                        current_config[setting_type] = {}
                    for action in ["warn", "timeout", "kick", "ban", "logs"]:
                        if action in settings:
                            if action not in current_config[setting_type]:
                                current_config[setting_type][action] = {}
                            current_config[setting_type][action][server_id] = settings[action]
                elif setting_type == "perks":
                    if setting_type not in current_config:
                        current_config[setting_type] = {}
                    if "snipe" in settings:
                        if "snipe" not in current_config[setting_type]:
                            current_config[setting_type]["snipe"] = {}
                        current_config[setting_type]["snipe"][server_id] = settings["snipe"]
                else:
                    if setting_type not in current_config:
                        current_config[setting_type] = {}
                    current_config[setting_type][server_id] = settings
                    
            configuration.update_one(
                {"_id": "config"},
                {"$set": current_config},
                upsert=True
            )
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving config: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/guild/<server_id>/roles")
@login_required
def get_guild_roles(server_id):
    try:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/roles", headers=headers)
        if response.status_code == 200:
            roles = response.json()
            roles.sort(key=lambda x: x.get('position', 0), reverse=True)
            return jsonify(roles)
        return jsonify([])
    except Exception as e:
        print(f"Error getting roles: {e}")
        return jsonify([])

@app.route("/api/guild/<server_id>/channels")
@login_required
def get_guild_channels(server_id):
    try:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/channels", headers=headers)
        if response.status_code == 200:
            channels = response.json()
            text_channels = [channel for channel in channels if channel.get('type') == 0]
            text_channels.sort(key=lambda x: x.get('position', 0))
            return jsonify(text_channels)
        return jsonify([])
    except Exception as e:
        print(f"Error getting channels: {e}")
        return jsonify([])

@app.route("/api/guild/<server_id>/roles/<role_id>")
@login_required
def get_guild_role(server_id, role_id):
    try:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/roles", headers=headers)
        if response.status_code == 200:
            roles = response.json()
            role = next((role for role in roles if str(role['id']) == str(role_id)), None)
            return jsonify(role if role else {})
        return jsonify({})
    except Exception as e:
        print(f"Error getting role: {e}")
        return jsonify({})

@app.route("/api/guild/<server_id>/channels/<channel_id>")
@login_required
def get_guild_channel(server_id, channel_id):
    try:
        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/channels", headers=headers)
        if response.status_code == 200:
            channels = response.json()
            channel = next((channel for channel in channels if str(channel['id']) == str(channel_id)), None)
            return jsonify(channel if channel else {})
        return jsonify({})
    except Exception as e:
        print(f"Error getting channel: {e}")
        return jsonify({})

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/terms")
def terms_of_service():
    return render_template("terms_of_service.html")

@app.route("/privacy")
def privacy_policy():
    return render_template("privacy_policy.html")

if __name__ == "__main__":
    app.run(debug=True)
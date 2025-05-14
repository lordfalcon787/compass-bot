from flask import Flask, render_template, request, session, redirect, url_for, jsonify
import os
from oauth import Oauth
from utils.mongo_connection import MongoConnection
from functools import wraps
import requests
from pymongo.errors import ServerSelectionTimeoutError

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
                         } if authorized else None)

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
                         client_id=BOT_CLIENT_ID)

@app.route("/server/<guild_id>/settings")
@login_required
def server_settings(guild_id):
    current_server = next((guild for guild in session['admin_guilds'] if guild['id'] == guild_id), None)
    if not current_server:
        return redirect(url_for("dashboard"))
    
    if not check_bot_in_guild(guild_id, session['access_token']):
        return redirect(url_for("dashboard"))
    
    return render_template("server_settings.html",
                         current_server=current_server,
                         user={
                             'name': session.get('user_logged_in_compass_dashboard'),
                             'avatar': session.get('user_avatar')
                         })

@app.route("/api/guild/<server_id>/config", methods=['GET'])
@login_required
def get_guild_config(server_id):
    try:
        if configuration:
            config = configuration.find_one({"guild_id": server_id})
            if config:
                return jsonify(config.get("settings", DEFAULT_CONFIG))
        return jsonify(DEFAULT_CONFIG)
    except Exception as e:
        print(f"Error getting config: {e}")
        return jsonify(DEFAULT_CONFIG)

@app.route("/api/guild/<server_id>/config", methods=['POST'])
@login_required
def save_guild_config(server_id):
    try:
        if configuration:
            config_data = request.json
            configuration.update_one(
                {"guild_id": server_id},
                {"$set": {"settings": config_data}},
                upsert=True
            )
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving config: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/api/guild/<server_id>/roles")
@login_required
def get_guild_roles(server_id):
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/roles", headers=headers)
    return jsonify(response.json())

@app.route("/api/guild/<server_id>/channels")
@login_required
def get_guild_channels(server_id):
    headers = {"Authorization": f"Bearer {session['access_token']}"}
    response = requests.get(f"https://discord.com/api/v10/guilds/{server_id}/channels", headers=headers)
    return jsonify(response.json())

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
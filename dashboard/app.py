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
    "quarantine": {
        "role": None
    },
    "utility": {
        "poll_roles": [],
        "lock_roles": [],
        "player_role": None,
        "event_manager_role": None,
        "role_cmd_access_roles": []
    },
    "suggestions": {
        "channel": None,
        "suggestion_role": None,
        "no_suggestions_role": None
    },
    "perks": {
        "snipe": []
    },
    "auto_responder": {
        "link_allowed": [],
        "words_allowed": [],
        "allowed": []
    },
    "auto_lock": {
        "enabled": False,
        "channels": []
    },
    "auction": {
        "channel": None,
        "role": None,
        "manager": None,
        "lock_on_end": False
    },
    "mafia_logs": {
        "channel": None
    },
    "counting": {
        "channel": None
    },
    "strike": {
        "log_channel": None,
        "announce_channel": None
    },
    "staff_list": {
        "roles": []
    },
    "pcms": {
        "roles": {},
        "requirements": []
    },
    "afk": {
        "roles": []
    },
    "highlight": {
        "access_roles": []
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
                
                # Handle moderation settings
                if "moderation" in config:
                    guild_config["moderation"] = {}
                    moderation_settings = config["moderation"]
                    for action in ["warn", "timeout", "kick", "ban", "logs"]:
                        if action in moderation_settings and server_id in moderation_settings[action]:
                            value = moderation_settings[action][server_id]
                            if action in ["warn", "timeout", "kick", "ban"]:
                                if isinstance(value, (list, tuple)):
                                    guild_config["moderation"][action] = [str(x) for x in value]
                                else:
                                    guild_config["moderation"][action] = []
                            elif action == "logs":
                                guild_config["moderation"][action] = str(value) if value else None
                        else:
                            if action in ["warn", "timeout", "kick", "ban"]:
                                guild_config["moderation"][action] = []
                            elif action == "logs":
                                guild_config["moderation"][action] = None
                else:
                    guild_config["moderation"] = DEFAULT_CONFIG.get("moderation", {})
                
                # Handle payout settings
                payout_config = {}
                payout_mappings = {"payout": "channel", "claim": "claim", "queue": "queue", "root": "role"}
                for backend_key, frontend_key in payout_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        payout_config[frontend_key] = str(config[backend_key][server_id])
                    else:
                        payout_config[frontend_key] = None
                guild_config["payout"] = payout_config
                
                # Handle quarantine settings
                if "quarantine" in config and server_id in config["quarantine"]:
                    guild_config["quarantine"] = {"role": str(config["quarantine"][server_id])}
                else:
                    guild_config["quarantine"] = {"role": None}
                
                # Handle utility settings
                utility_config = {}
                utility_mappings = {
                    "poll_role": "poll_roles",
                    "lock_role": "lock_roles", 
                    "player_role": "player_role",
                    "event_manager_role": "event_manager_role",
                    "role_cmd_access_roles": "role_cmd_access_roles"
                }
                
                for backend_key, frontend_key in utility_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        value = config[backend_key][server_id]
                        if frontend_key in ["poll_roles", "lock_roles", "role_cmd_access_roles"]:
                            if isinstance(value, (list, tuple)):
                                utility_config[frontend_key] = [str(x) for x in value]
                            else:
                                utility_config[frontend_key] = []
                        else:
                            utility_config[frontend_key] = str(value) if value else None
                    else:
                        if frontend_key in ["poll_roles", "lock_roles", "role_cmd_access_roles"]:
                            utility_config[frontend_key] = []
                        else:
                            utility_config[frontend_key] = None
                guild_config["utility"] = utility_config
                
                # Handle suggestions settings
                suggestions_config = {}
                suggestion_mappings = {
                    "suggestions": "channel",
                    "suggestion_role": "suggestion_role", 
                    "no_suggestions": "no_suggestions_role"
                }
                
                for backend_key, frontend_key in suggestion_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        suggestions_config[frontend_key] = str(config[backend_key][server_id])
                    else:
                        suggestions_config[frontend_key] = None
                guild_config["suggestions"] = suggestions_config
                
                # Handle perks settings
                if "perks" in config:
                    guild_config["perks"] = {}
                    perks_settings = config["perks"]
                    if "snipe" in perks_settings and server_id in perks_settings["snipe"]:
                        value = perks_settings["snipe"][server_id]
                        if isinstance(value, (list, tuple)):
                            guild_config["perks"]["snipe"] = [str(x) for x in value]
                        else:
                            guild_config["perks"]["snipe"] = []
                    else:
                        guild_config["perks"]["snipe"] = []
                else:
                    guild_config["perks"] = {"snipe": []}
                
                # Handle auto_responder settings
                auto_responder_config = {}
                ar_mappings = {"link_allowed": "link_allowed", "words_allowed": "words_allowed", "allowed": "allowed"}
                for backend_key, frontend_key in ar_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        value = config[backend_key][server_id]
                        if isinstance(value, (list, tuple)):
                            auto_responder_config[frontend_key] = [str(x) for x in value]
                        else:
                            auto_responder_config[frontend_key] = []
                    else:
                        auto_responder_config[frontend_key] = []
                guild_config["auto_responder"] = auto_responder_config
                
                # Handle auto_lock settings
                auto_lock_config = {"enabled": False, "channels": []}
                if "auto_lock" in config and server_id in config["auto_lock"]:
                    auto_lock_config["enabled"] = bool(config["auto_lock"][server_id])
                if "auto_lock_channels" in config and server_id in config["auto_lock_channels"]:
                    value = config["auto_lock_channels"][server_id]
                    if isinstance(value, (list, tuple)):
                        auto_lock_config["channels"] = [str(x) for x in value]
                    else:
                        auto_lock_config["channels"] = []
                guild_config["auto_lock"] = auto_lock_config
                
                # Handle auction settings
                auction_config = {}
                auction_mappings = {"auction": "channel", "auction_role": "role", "auction_manager": "manager", "lock_on_end": "lock_on_end"}
                for backend_key, frontend_key in auction_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        value = config[backend_key][server_id]
                        if frontend_key == "lock_on_end":
                            auction_config[frontend_key] = bool(value)
                        else:
                            auction_config[frontend_key] = str(value) if value else None
                    else:
                        if frontend_key == "lock_on_end":
                            auction_config[frontend_key] = False
                        else:
                            auction_config[frontend_key] = None
                guild_config["auction"] = auction_config
                
                # Handle mafia_logs settings
                if "mafia_logs" in config and server_id in config["mafia_logs"]:
                    guild_config["mafia_logs"] = {"channel": str(config["mafia_logs"][server_id])}
                else:
                    guild_config["mafia_logs"] = {"channel": None}
                
                # Handle counting settings
                if "counting" in config and server_id in config["counting"]:
                    guild_config["counting"] = {"channel": str(config["counting"][server_id])}
                else:
                    guild_config["counting"] = {"channel": None}
                
                # Handle strike settings
                strike_config = {}
                strike_mappings = {"strike_log": "log_channel", "strike_announce": "announce_channel"}
                for backend_key, frontend_key in strike_mappings.items():
                    if backend_key in config and server_id in config[backend_key]:
                        strike_config[frontend_key] = str(config[backend_key][server_id])
                    else:
                        strike_config[frontend_key] = None
                guild_config["strike"] = strike_config
                
                # Handle staff_list settings
                if "staff_list" in config and server_id in config["staff_list"]:
                    value = config["staff_list"][server_id]
                    if isinstance(value, (list, tuple)):
                        guild_config["staff_list"] = {"roles": [str(x) for x in value]}
                    else:
                        guild_config["staff_list"] = {"roles": []}
                else:
                    guild_config["staff_list"] = {"roles": []}
                
                # Handle pcms settings
                pcms_config = {"roles": {}, "requirements": []}
                if "pcms" in config and server_id in config["pcms"]:
                    pcms_data = config["pcms"][server_id]
                    if isinstance(pcms_data, dict):
                        pcms_config["roles"] = {str(k): v for k, v in pcms_data.items()}
                if "pcms_requirements" in config and server_id in config["pcms_requirements"]:
                    value = config["pcms_requirements"][server_id]
                    if isinstance(value, (list, tuple)):
                        pcms_config["requirements"] = [str(x) for x in value]
                guild_config["pcms"] = pcms_config
                
                # Handle afk settings
                if "afk" in config and server_id in config["afk"]:
                    value = config["afk"][server_id]
                    if isinstance(value, (list, tuple)):
                        guild_config["afk"] = {"roles": [str(x) for x in value]}
                    else:
                        guild_config["afk"] = {"roles": []}
                else:
                    guild_config["afk"] = {"roles": []}
                
                # Handle highlight settings
                if "highlight" in config and server_id in config["highlight"]:
                    value = config["highlight"][server_id]
                    if isinstance(value, (list, tuple)):
                        guild_config["highlight"] = {"access_roles": [str(x) for x in value]}
                    else:
                        guild_config["highlight"] = {"access_roles": []}
                else:
                    guild_config["highlight"] = {"access_roles": []}
                
                print(f"Processed guild config: {guild_config}")
                return jsonify(guild_config)
        
        print("No config found, returning defaults")
        return jsonify(DEFAULT_CONFIG)
    except Exception as e:
        print(f"Error getting config: {e}")
        import traceback
        traceback.print_exc()
        return jsonify(DEFAULT_CONFIG)

@app.route("/api/guild/<server_id>/config", methods=['POST'])
@login_required
def save_guild_config(server_id):
    try:
        if configuration is not None:
            print("Saving config")
            config_data = request.json
            print(f"Received config data: {config_data}")
            
            current_config = configuration.find_one({"_id": "config"}) or {}
            print(f"Current config before update: {current_config}")
            
            for setting_type, settings in config_data.items():
                if setting_type == "moderation":
                    moderation_mappings = {"warn": "warn", "timeout": "timeout", "kick": "kick", "ban": "ban", "logs": "logs"}
                    for frontend_key, backend_key in moderation_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if frontend_key == "logs":
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                            else:
                                if isinstance(value, list) and value:
                                    current_config[backend_key][server_id] = [str(role_id) for role_id in value if role_id]
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                
                elif setting_type == "payout":
                    payout_mappings = {"channel": "payout", "claim": "claim", "queue": "queue", "role": "root"}
                    for frontend_key, backend_key in payout_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if frontend_key == "role":
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                            else:
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                
                elif setting_type == "quarantine":
                    value = settings.get("role")
                    if "quarantine" not in current_config:
                        current_config["quarantine"] = {}
                    if value and value != "null":
                        current_config["quarantine"][server_id] = str(value)
                    else:
                        if server_id in current_config["quarantine"]:
                            del current_config["quarantine"][server_id]
                
                elif setting_type == "utility":
                    utility_mappings = {
                        "poll_roles": "poll_roles",
                        "lock_roles": "lock_roles",
                        "player_role": "player_role",
                        "event_manager_role": "event_manager_role",
                        "role_cmd_access_roles": "role_cmd_access_roles"
                    }
                    for frontend_key, backend_key in utility_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if frontend_key in ["player_role", "event_manager_role"]:
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                            else:
                                if isinstance(value, list) and value:
                                    current_config[backend_key][server_id] = [str(role_id) for role_id in value if role_id]
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                
                elif setting_type == "suggestions":
                    suggestions_mappings = {"channel": "suggestions", "suggestion_role": "suggestion_role", "no_suggestions_role": "no_suggestions_role"}
                    for frontend_key, backend_key in suggestions_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if frontend_key == "channel":
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                            else:
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                
                elif setting_type == "perks":
                    if setting_type not in current_config:
                        current_config[setting_type] = {}
                    value = settings.get("snipe")
                    if "snipe" not in current_config[setting_type]:
                        current_config[setting_type]["snipe"] = {}
                    if isinstance(value, list) and value:
                        current_config[setting_type]["snipe"][server_id] = [str(role_id) for role_id in value if role_id]
                    else:
                        if server_id in current_config[setting_type]["snipe"]:
                            del current_config[setting_type]["snipe"][server_id]
                
                elif setting_type == "auto_responder":
                    ar_mappings = {"link_allowed": "link_allowed", "words_allowed": "words_allowed", "allowed": "allowed"}
                    for frontend_key, backend_key in ar_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if isinstance(value, list) and value:
                                current_config[backend_key][server_id] = [str(role_id) for role_id in value if role_id]
                            else:
                                if server_id in current_config[backend_key]:
                                    del current_config[backend_key][server_id]
                
                elif setting_type == "auto_lock":
                    value_enabled = settings.get("enabled")
                    value_channels = settings.get("channels")
                    if "auto_lock" not in current_config:
                        current_config["auto_lock"] = {}
                    if value_enabled:
                        current_config["auto_lock"][server_id] = bool(value_enabled)
                    else:
                        if server_id in current_config["auto_lock"]:
                            del current_config["auto_lock"][server_id]
                    if "auto_lock_channels" not in current_config:
                        current_config["auto_lock_channels"] = {}
                    if isinstance(value_channels, list) and value_channels:
                        current_config["auto_lock_channels"][server_id] = [str(channel_id) for channel_id in value_channels if channel_id]
                    else:
                        if server_id in current_config["auto_lock_channels"]:
                            del current_config["auto_lock_channels"][server_id]
                
                elif setting_type == "auction":
                    auction_mappings = {"channel": "auction", "role": "auction_role", "manager": "auction_manager", "lock_on_end": "lock_on_end"}
                    for frontend_key, backend_key in auction_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if frontend_key == "lock_on_end":
                                if value:
                                    current_config[backend_key][server_id] = bool(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                            else:
                                if value and value != "null":
                                    current_config[backend_key][server_id] = str(value)
                                else:
                                    if server_id in current_config[backend_key]:
                                        del current_config[backend_key][server_id]
                
                elif setting_type == "mafia_logs":
                    value = settings.get("channel")
                    if "mafia_logs" not in current_config:
                        current_config["mafia_logs"] = {}
                    if value and value != "null":
                        current_config["mafia_logs"][server_id] = str(value)
                    else:
                        if server_id in current_config["mafia_logs"]:
                            del current_config["mafia_logs"][server_id]
                
                elif setting_type == "counting":
                    value = settings.get("channel")
                    if "counting" not in current_config:
                        current_config["counting"] = {}
                    if value and value != "null":
                        current_config["counting"][server_id] = str(value)
                    else:
                        if server_id in current_config["counting"]:
                            del current_config["counting"][server_id]
                
                elif setting_type == "strike":
                    strike_mappings = {"log_channel": "strike_log", "announce_channel": "strike_announce"}
                    for frontend_key, backend_key in strike_mappings.items():
                        if frontend_key in settings:
                            if backend_key not in current_config:
                                current_config[backend_key] = {}
                            value = settings[frontend_key]
                            if value and value != "null":
                                current_config[backend_key][server_id] = str(value)
                            else:
                                if server_id in current_config[backend_key]:
                                    del current_config[backend_key][server_id]
                
                elif setting_type == "staff_list":
                    value = settings.get("roles")
                    if "staff_list" not in current_config:
                        current_config["staff_list"] = {}
                    if isinstance(value, list) and value:
                        current_config["staff_list"][server_id] = [str(role_id) for role_id in value if role_id]
                    else:
                        if server_id in current_config["staff_list"]:
                            del current_config["staff_list"][server_id]
                
                elif setting_type == "pcms":
                    value_roles = settings.get("roles")
                    value_reqs = settings.get("requirements")
                    if "pcms" not in current_config:
                        current_config["pcms"] = {}
                    if value_roles and isinstance(value_roles, dict) and value_roles:
                        current_config["pcms"][server_id] = value_roles
                    else:
                        if server_id in current_config["pcms"]:
                            del current_config["pcms"][server_id]
                    if "pcms_requirements" not in current_config:
                        current_config["pcms_requirements"] = {}
                    if isinstance(value_reqs, list) and value_reqs:
                        current_config["pcms_requirements"][server_id] = [str(role_id) for role_id in value_reqs if role_id]
                    else:
                        if server_id in current_config["pcms_requirements"]:
                            del current_config["pcms_requirements"][server_id]
                
                elif setting_type == "afk":
                    value = settings.get("roles")
                    if "afk" not in current_config:
                        current_config["afk"] = {}
                    if isinstance(value, list) and value:
                        current_config["afk"][server_id] = [str(role_id) for role_id in value if role_id]
                    else:
                        if server_id in current_config["afk"]:
                            del current_config["afk"][server_id]
                
                elif setting_type == "highlight":
                    value = settings.get("access_roles")
                    if "highlight" not in current_config:
                        current_config["highlight"] = {}
                    if isinstance(value, list) and value:
                        current_config["highlight"][server_id] = [str(role_id) for role_id in value if role_id]
                    else:
                        if server_id in current_config["highlight"]:
                            del current_config["highlight"][server_id]
                
                else:
                    # Generic handling for other settings
                    if setting_type not in current_config:
                        current_config[setting_type] = {}
                    current_config[setting_type][server_id] = settings
            
            print(f"Final config to save: {current_config}")
            
            configuration.update_one(
                {"_id": "config"},
                {"$set": current_config},
                upsert=True
            )
            
            print("Config saved successfully")
        return jsonify({"status": "success"})
    except Exception as e:
        print(f"Error saving config: {e}")
        import traceback
        traceback.print_exc()
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
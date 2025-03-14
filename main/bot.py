import nextcord
import json
import psutil

from datetime import datetime
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

with open("config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]
BOT_OWNER = config["bot_owner"]

RC_ICON = "https://i.imgur.com/K5L7kxl.png"
RC_BANNER = "https://i.imgur.com/kL6BSmK.jpeg"

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

mongo = MongoConnection.get_instance()
client = mongo.get_client()
db = mongo.get_db()
misccollection = db["Misc"]
itemcollection = db["Items"]

def get_prefix(bot, message):
    with open("prefixes.json", "r") as file:
        prefixes = json.load(file)
    
    try:
        prefix = prefixes[str(message.guild.id)]
    except:
        prefix = []
    prefix.append("<@1291996619490984037> ")
    return prefix


class UnfilteredBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.launch_time = datetime.now()

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        if message.content.startswith('<@1291996619490984037> '):
            temp_content = message.content.replace('<@1291996619490984037> ', '', 1)
            ctx.message.content = temp_content
        
        await self.invoke(ctx)
    
    async def invoke(self, ctx):
        if ctx.command is None:
            return
        await super().invoke(ctx)


intents = nextcord.Intents.all()
bot = UnfilteredBot(
    command_prefix=get_prefix, 
    owner_id = 1166134423146729563, 
    intents=intents,
    activity=nextcord.Activity(type=nextcord.ActivityType.playing, name="Navigating the Sea"),
    status=nextcord.Status.online, 
    help_command=None
)

extensions = misccollection.find_one({"_id": "extensions"})["extensions"]

if __name__ == "__main__":
    for extension in extensions:
        bot.load_extension(extension)

async def ban_check(interaction: nextcord.Interaction):
    banned_users = misccollection.find_one({"_id": "bot_banned"})
    if banned_users:
        if str(interaction.user.id) in banned_users:
            embed = nextcord.Embed(title="Bot Banned", description=f"You are banned from using this bot. Please contact the bot owner if you believe this is an error. \n\n **Reason:** {banned_users[str(interaction.user.id)]}", color=16711680)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        else:
            return True
    else:
        return True

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"An error occurred: {e}")
    version = await get_version()
    print(f"Bot Version: {version}")

async def get_version():
    bot_version = misccollection.find_one({"_id": "bot_version"})["version"]
    bot_version = list(str(bot_version))
    version = ""
    length = len(bot_version)
    num = 0
    for letter in bot_version:
        if num != length - 1:
            version = f"{version}{letter}."
        else:
            version = f"{version}{letter}"
        num += 1
    return version

@bot.event
async def on_guild_join(guild):
    with open("prefixes.json", "r") as file:
        prefixes = json.load(file)
    if str(guild.id) not in prefixes:
        prefixes[str(guild.id)] = ["-"]
    with open("prefixes.json", "w") as file:
        json.dump(prefixes, file, indent=4)

@bot.command(name="stats", aliases=["statistics", "status"])
async def stats_cmd(ctx):
    time_send_1 = datetime.now()
    msg = await ctx.reply("Sending request...", mention_author=False)
    time_send_2 = datetime.now()
    time_send = (time_send_2 - time_send_1).total_seconds() * 1000
    time_send = round(time_send, 2)
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    net_io = psutil.net_io_counters()
    uptime = datetime.now() - bot.launch_time
    latency = round(bot.latency * 1000)

    mongo_stats = client.admin.command('serverStatus')
    time_1 = datetime.now()
    itemcollection.insert_one({"_id": "test"})
    time_2 = datetime.now()
    mongo_latency = (time_2 - time_1).total_seconds() * 1000
    mongo_latency = round(mongo_latency, 2)
    itemcollection.delete_one({"_id": "test"})

    embed = nextcord.Embed(title="Bot Statistics", color=3447003)
    embed.add_field(name="CPU Usage", value=f"{cpu_usage}%", inline=True)
    embed.add_field(name="RAM Usage", value=f"{ram_usage}%", inline=True)
    embed.add_field(name="Network Sent", value=f"{net_io.bytes_sent / (1024 ** 2):.2f} MB", inline=True)
    embed.add_field(name="Network Received", value=f"{net_io.bytes_recv / (1024 ** 2):.2f} MB", inline=True)
    days = int(uptime.total_seconds() // 86400)
    hours = int((uptime.total_seconds() % 86400) // 3600)
    minutes = int((uptime.total_seconds() % 3600) // 60)
    seconds = int(uptime.total_seconds() % 60)
    embed.add_field(name="Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
    embed.add_field(name="Bot Latency", value=f"{latency} ms", inline=True)
    embed.add_field(name="API Latency", value=f"{time_send} ms", inline=True)
    embed.add_field(name="MongoDB Latency", value=f"{mongo_latency} ms", inline=True)
    embed.add_field(name="MongoDB Stats", value=f"Connections: {mongo_stats['connections']['current']}, Queries: {mongo_stats['opcounters']['query']}", inline=True)

    await msg.edit(content=None, embed=embed)

@bot.command(name="version")
async def version_cmd(ctx):
    if ctx.author.id != BOT_OWNER:
        return
    split = ctx.message.content.split(" ")
    if len(split) == 1:
        version = str(misccollection.find_one({"_id": "bot_version"})["version"])
        version_str = str(version)
        new_version = '.'.join(version_str)
        await ctx.reply(content=f"Bot Version: {new_version}", mention_author=False)
    else:
        version = split[1]
        old_version = version
        version = version.replace(".", "")
        version = int(version)
        misccollection.update_one({"_id": "bot_version"}, {"$set": {"version": version}})
        await ctx.reply(content=f"Set version to {old_version}", mention_author=False)

@bot.command(name="addextension")
async def addextension_cmd(ctx, extension: str):
    if ctx.author.id != BOT_OWNER:
        return
    extension = extension.lower()
    current_extensions = misccollection.find_one({"_id": "extensions"})["extensions"]
    if extension in current_extensions:
        await ctx.reply(content=f"Extension already exists.", mention_author=False)
        return
    current_extensions.append(extension)
    current_extensions.sort()
    misccollection.update_one({"_id": "extensions"}, {"$set": {"extensions": current_extensions}})
    await ctx.message.add_reaction(GREEN_CHECK)

@bot.command(name="sortextensions")
async def sortextensions_cmd(ctx):
    if ctx.author.id != BOT_OWNER:
        return
    current_extensions = misccollection.find_one({"_id": "extensions"})["extensions"]
    current_extensions.sort()
    misccollection.update_one({"_id": "extensions"}, {"$set": {"extensions": current_extensions}})
    await ctx.message.add_reaction(GREEN_CHECK)

@bot.command(name="removeextension")
async def removeextension_cmd(ctx, extension: str):
    if ctx.author.id != BOT_OWNER:
        return
    extension = extension.lower()
    current_extensions = misccollection.find_one({"_id": "extensions"})["extensions"]
    if extension not in current_extensions:
        await ctx.reply(content=f"Extension not found.", mention_author=False)
        return
    current_extensions.remove(extension)
    current_extensions.sort()
    misccollection.update_one({"_id": "extensions"}, {"$set": {"extensions": current_extensions}})
    await ctx.message.add_reaction(GREEN_CHECK)

@bot.command(name="getprefixes")
async def getprefixes_cmd(ctx):
    if ctx.author.id != BOT_OWNER:
        return
    await ctx.author.send(file=nextcord.File("prefixes.json"))

@bot.command(name="getitems")
async def getitems_cmd(ctx):
    items = list(itemcollection.find({}))
    await ctx.reply("Items have been exported. Please check your Discord DMs for the file.", mention_author=False)
    with open("items.json", "w") as json_file:
        json.dump(items, json_file, default=str)
    await ctx.author.send(file=nextcord.File("items.json"))

@bot.command(name="prefix")    
async def prefix_cmd(ctx):
    content = ctx.message.content
    split = content.split(" ")
    with open("prefixes.json", "r") as file:
            prefixes = json.load(file)

    if str(ctx.guild.id) not in prefixes:
        prefixes[str(ctx.guild.id)] = []

    if len(split) == 1:
        if str(ctx.guild.id) in prefixes:
            prefix_list = prefixes[str(ctx.guild.id)]
            descp = "1. <@1291996619490984037>"
            num = 2
            for prefix in prefix_list:
                descp = f"{descp}\n{num}. {prefix}"
                num += 1
            embed = nextcord.Embed(title="Current Prefixes", description=f"{descp}", color=0x00ff00)
        await ctx.reply(embed=embed, mention_author=False)
        return
    
    if not ctx.author.guild_permissions.administrator:
        await ctx.reply("You do not have permission to use this command.", mention_author=False)
        return
    
    args = ["remove", "add", "set"]
    if split[1] not in args:
        await ctx.reply("Invalid argument.", mention_author=False)
        return
    
    if split[1] == "remove":
        if len(split) == 2:
            await ctx.reply("Please specify a prefix to remove.", mention_author=False)
            return
        prefix = split[2]
        if prefix not in prefixes[str(ctx.guild.id)]:
            await ctx.reply("Prefix not found.", mention_author=False)
            return
        prefixes[str(ctx.guild.id)].remove(prefix)
        with open("prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=4)
        await ctx.reply("Prefix removed.", mention_author=False)
        return
    
    if split[1] == "add":
        if len(split) == 2:
            await ctx.reply("Please specify a prefix to add.", mention_author=False)
            return
        prefix = split[2]
        if prefix in prefixes[str(ctx.guild.id)]:
            await ctx.reply("Prefix already exists.", mention_author=False)
            return
        prefixes[str(ctx.guild.id)].append(prefix)
        with open("prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=4)
        await ctx.reply("Prefix added.", mention_author=False)
        return

    if split[1] == "set":
        if len(split) == 2:
            await ctx.reply("Please specify a prefix to set.", mention_author=False)
            return
        prefix = split[2]
        prefixes[str(ctx.guild.id)] = [prefix]
        with open("prefixes.json", "w") as file:
            json.dump(prefixes, file, indent=4)
        await ctx.reply("Prefix set.", mention_author=False)
        return

@bot.command(name="ping")
async def latency_cmd(ctx):
    latency = bot.latency * 1000
    await ctx.send(f"Pong! {latency} milliseconds.")

bot.run(BOT_TOKEN)


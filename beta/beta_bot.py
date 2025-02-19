import nextcord
from datetime import datetime
from nextcord.ext import commands
import json

with open("beta_config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]

RC_ICON = "https://i.imgur.com/K5L7kxl.png"
RC_BANNER = "https://i.imgur.com/kL6BSmK.jpeg"

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

from beta_mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
client = mongo.get_client()
db = mongo.get_db()
collection = db["Items"]

class UnfilteredBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.launch_time = datetime.now()

    async def process_commands(self, message):
        ctx = await self.get_context(message)
        await self.invoke(ctx)
    
    async def invoke(self, ctx):
        if ctx.command is None:
            return
        await super().invoke(ctx)


intents = nextcord.Intents.all()
intents.message_content = True
intents.reactions = True
bot = UnfilteredBot(
    command_prefix=["c!"], 
    owner_id = 1166134423146729563, 
    intents=intents,
    activity=nextcord.Activity(type=nextcord.ActivityType.playing, name="Navigating the Ocean"),
    status=nextcord.Status.online, 
    help_command=None
)

extensions = ["cogs.beta_payouts", "cogs.beta_config"]

if __name__ == "__main__":
    for extension in extensions:
        bot.load_extension(extension)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(f"An error occurred: {e}")

@bot.command(name="uploaditems")
async def uploaditems_cmd(ctx):
    if not ctx.author.guild_permissions.administrator:
        return
    if ctx.author.id != 1166134423146729563:
        return
    items = None
    with open("items.json", "r") as file:
        items = json.load(file)
    for item in items:
        collection.insert_one(item)
    await ctx.send("Items uploaded.")

@bot.command(name="ping")
async def latency_cmd(ctx):
    latency = bot.latency * 1000
    await ctx.send(f"Pong! {latency} milliseconds.")

bot.run(BOT_TOKEN)


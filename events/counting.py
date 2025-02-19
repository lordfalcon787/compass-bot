import nextcord
from nextcord.ext import commands, tasks
import json
from utils.mongo_connection import MongoConnection

with open("config.json", "r") as file:
    config = json.load(file)

GREEN_CHECK = "<:green_check:1218286675508199434>"
RED_X = "<:red_x:1218287859963007057>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Counting"]
configuration = db["Configuration"]

class Counting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}

    @tasks.loop(seconds=10)
    async def update_cache(self):
        config = configuration.find_one({"_id": "config"})
        config = config["counting"]
        for key in config.keys():
            self.cache[key] = config[key]

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Counting cog loaded.")
        self.update_cache.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            guild = str(message.guild.id)
            channel = self.cache.get(guild)
            if message.channel.id != channel:
                return
        except:
            return
        try:
            if len(message.content.split(" ")) == 1:
                await self.count(message)
            else:
                return
        except:
            return
    
    async def count(self, message):
        msg = message.content.replace(",", "")
        msg = msg.replace(" ", "")
        try:
            num = int(msg)
        except:
            return
        
        doc = collection.find_one({"_id": f"current_count_{message.guild.id}"})
        if not doc:
            doc = {"Number": 0, "Last": 11}
            collection.insert_one({"_id": f"current_count_{message.guild.id}", "Number": 0, "Last": 11})
        last_count = doc["Number"]
        last_counter = doc["Last"]
        if num <= last_count:
            await message.channel.send(f"{RED_X} {message.author.mention} RUINED IT at {num}!! The next number is **1**.")
            await message.add_reaction(RED_X)
            collection.update_one({"_id": f"current_count_{message.guild.id}"}, {"$set": {"Number": 0, "Last": 11}})
            return
        elif message.author.id == last_counter:
            await message.channel.send(f"{RED_X} {message.author.mention} RUINED IT at {num}!! You cannot count twice in a row! The next number is **1**.")
            await message.add_reaction(RED_X)
            collection.update_one({"_id": f"current_count_{message.guild.id}"}, {"$set": {"Number": 0, "Last": 11}})
            return
        elif num - last_count > 1:
            await message.channel.send(f"{RED_X} {message.author.mention} RUINED IT at {num}!! You cannot skip numbers! The next number is **1**.")
            await message.add_reaction(RED_X)
            collection.update_one({"_id": f"current_count_{message.guild.id}"}, {"$set": {"Number": 0, "Last": 11}})
            return
        else:
            await message.add_reaction(GREEN_CHECK)
            collection.update_one({"_id": f"current_count_{message.guild.id}"}, {"$set": {"Number": num, "Last": message.author.id}})

def setup(bot):
    bot.add_cog(Counting(bot))
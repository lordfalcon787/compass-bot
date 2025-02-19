import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Items"]

class ItemUpdate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Item Update cog loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != 270904126974590976:
            return
        elif not message.embeds or message.embeds[0].description is None:
            return
        elif "You own **" not in message.embeds[0].description:
            return
        else:
            item = message.embeds[0].title
            value = message.embeds[0].fields[1].value
            value = value.split("\n")[0]
            value = value.split("⏣ ")[1]
            value = value.replace(",", "")
            value = int(value)
            try:
                collection.insert_one({"_id": item, "price": value})
            except:
                collection.update_one({"_id": item}, {"$set": {"price": value}})

def setup(bot):
    bot.add_cog(ItemUpdate(bot))
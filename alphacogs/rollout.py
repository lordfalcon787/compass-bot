import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Rollout"]

class Rollout(nextcord.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Rollout cog loaded")

def setup(bot):
    bot.add_cog(Rollout(bot))
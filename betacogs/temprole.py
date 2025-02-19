import nextcord
from nextcord.ext import commands
import json
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Misc"]

class Temprole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def temprole(self, user_id, role_id, remove_at):
        temp_role_data = {
            "user_id": user_id,
            "role_id": role_id,
            "remove_at": remove_at,
        }
        member = self.bot.get_member(user_id)
        member.add_roles(role_id)
        highest_key = 0
        keys = collection.find_one("_id", "temproles").keys()
        highest_key = len(keys)
        collection.update_one({"_id": "temproles"}, {"$set": {highest_key: temp_role_data}})

    @commands.command(name="onbreak")
    async def onbreak(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply("You are not authorized to use this command")
            return
        context = ctx.split(" ")
        if len(context) < 3:
            await ctx.reply("Correct syntax is `[p]onbreak [user] [duration]`")
            return
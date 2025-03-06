import nextcord
from nextcord.ext import commands
import random
from datetime import datetime, timedelta

fivehundred = 1334990776702341150
billion = 1334990830242365472

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Fun Commands"]
acollection = db["Admin"]

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Fun Commands cog is ready")

    @commands.command(name="kill")
    async def kill(self, ctx: commands.Context):
        roles = [role.id for role in ctx.author.roles]
        if fivehundred  not in roles and ctx.author.id != 748339732605436055:
            await ctx.message.add_reaction(RED_X)
            return
        
        guild_channels = [channel.name for channel in ctx.guild.channels]
        if "mafia" in guild_channels:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You cannot use this command while a mafia game is active.", mention_author=False)
            return
        
        membertwo = ctx.guild.get_member(ctx.author.id)
        
        split = ctx.message.content.split(" ")

        if len(split) == 1:
            try:
                await membertwo.timeout(datetime.now() + timedelta(seconds=30))
            except:
                pass
            await ctx.message.add_reaction(GREEN_CHECK)
            await ctx.reply("Successfully timed you out for 30 seconds.", mention_author=False)
            return
        
        cooldown = 300

        if billion in roles:
            cooldown = 180
        
        doc = collection.find_one({"_id": "kill_cmd"})
        other_doc = collection.find_one({"_id": "kill_cmd_whitelist"})
        whitelist = other_doc["whitelist"]
        if doc is None:
            pass
        elif str(ctx.author.id) not in doc:
            pass
        else:
            if int(datetime.now().timestamp()) - doc[str(ctx.author.id)] < cooldown:
                await ctx.message.add_reaction(RED_X)
                time = doc[str(ctx.author.id)] + cooldown
                await ctx.reply(f"You can only use this command once every 5 minutes. You can use it again <t:{time}:R>", mention_author=False)
                return

        user = split[1]
        user = user.replace("<", "").replace("@", "").replace(">", "")
        member = ctx.guild.get_member(int(user))
        user = await self.bot.fetch_user(int(user))
        chance = random.randint(1, 100)

        if user.id in whitelist:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("This user is whitelisted, you cannot time them out.", mention_author=False)
            return
        
        if ctx.author.id in whitelist:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You are whitelisted, you cannot time out users.", mention_author=False)
            return
        
        if member.communication_disabled_until and member.communication_disabled_until > datetime.now():
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("This user is already timed out.", mention_author=False)
            return

        if member.guild_permissions.administrator:
            try:
                await membertwo.timeout(datetime.now() + timedelta(seconds=30))
            except:
                pass
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You cannot time out an admin, it backfires.", mention_author=False)
            return
        elif member.bot:
            await ctx.message.add_reaction(RED_X)
            return

        if chance >= 50:
            try:
                await member.timeout(datetime.now() + timedelta(seconds=30))
            except:
                pass
            await ctx.message.add_reaction(GREEN_CHECK)
            await ctx.reply("Successfully timed out the user for 30 seconds.", mention_author=False)
        else:
            try:
                await membertwo.timeout(datetime.now() + timedelta(seconds=30))
            except:
                pass
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("Backfired!", mention_author=False)

        time = int(datetime.now().timestamp())
        collection.update_one({"_id": "kill_cmd"}, {"$set": {f"{ctx.author.id}": time}}, upsert=True)

    @commands.command(name="message")
    async def message(self, ctx: commands.Context):
        pass

    @commands.command(name="spamping")
    async def spamping(self, ctx: commands.Context):
        bot_admins = acollection.find_one({"_id": "bot_admins"})
        if not ctx.author.guild_permissions.administrator and ctx.author.id not in bot_admins["admins"]:
            await ctx.message.add_reaction(RED_X)
            return
        
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            await ctx.message.add_reaction(RED_X)
            return
        
        message = split[1]
        message = message.replace("<", "").replace("@", "").replace(">", "")
        message = int(message)
        user = self.bot.get_user(message)
        if user is None:
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")

def setup(bot):
    bot.add_cog(FunCommands(bot))





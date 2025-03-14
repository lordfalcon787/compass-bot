import nextcord
from nextcord.ext import commands

from utils.mongo_connection import MongoConnection
from datetime import datetime

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]
collection = db["Moderation"]

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Moderation cog loaded.")

    @commands.command(name="warn")
    async def warn_cmd(self, ctx, member: nextcord.Member, *, reason: str):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["warn"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No warn configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return

    @commands.command(name="timeout")
    async def timeout_cmd(self, ctx, member: nextcord.Member, time: str, *, reason: str):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["timeout"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No timeout configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return

    @commands.command(name="kick")
    async def kick_cmd(self, ctx, member: nextcord.Member, *, reason: str):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["kick"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No kick configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return

    @commands.command(name="ban")
    async def ban_cmd(self, ctx, member: nextcord.Member, *, reason: str):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["ban"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No ban configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
    
    @commands.command(name="unban")
    async def unban_cmd(self, ctx, member: nextcord.Member, *, reason: str):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["ban"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No ban configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return  

    @commands.command(name="removetimeout", aliases=["untimeout", "rto"])
    async def removetimeout_cmd(self, ctx, member: nextcord.Member):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["timeout"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No timeout configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
    
    @commands.command(name="removewarn", aliases=["rwarn", "deletewarn", "delwarn"])
    async def removewarn_cmd(self, ctx, member: nextcord.Member, amount: int):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["warn"]
        config = config.get(str(ctx.guild.id))
        if not config:
            await ctx.reply("No warn configuration found for this guild.", mention_author=False)
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        
    
    

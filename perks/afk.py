import nextcord
from nextcord.ext import commands, tasks, application_checks
from datetime import datetime
import asyncio

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["AFK"]
configuration = db["Configuration"]


class AFK(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.ignore_cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        self.afk_check.start()
        self.ignore_check.start()
        print("AFK cog loaded")

    @tasks.loop(seconds=10)
    async def afk_check(self):
        docs = list(collection.find())
        for doc in docs:
            if doc["_id"] == "afk_ignore":
                continue
            guild = doc["_id"].split(".")[1]
            self.cache[guild] = doc

    @tasks.loop(seconds=10)
    async def ignore_check(self):
        doc = collection.find_one({"_id": "afk_ignore"})
        if not doc:
            return
        self.ignore_cache = doc

    @commands.command(name="afk")
    async def afk_command(self, ctx):
        split = ctx.message.content.split(" ")
        args = ["clear", "ignore", "ignored", "remove"]
        doc = collection.find_one({"_id": f"afk.{ctx.guild.id}"})
        allowed = configuration.find_one({"_id": "config"})["afk"]
        if str(ctx.guild.id) not in allowed:
            allowed = []
        else:
            allowed = allowed[str(ctx.guild.id)]
        if not doc:
            doc = {}
        user_roles = [role.id for role in ctx.author.roles]
        if not any(role in allowed for role in user_roles) and not ctx.author.guild_permissions.administrator:
            await ctx.reply(content="You do not have permission to use this command.", mention_author=False)
            return
        if len(split) == 1:
            if str(ctx.author.id) in doc:
                await ctx.reply(content="You are already AFK.", mention_author=False)
                return
            collection.update_one({"_id": f"afk.{ctx.guild.id}"}, {"$set": {f"{ctx.author.id}.reason": "AFK", f"{ctx.author.id}.time": int(datetime.now().timestamp())}}, upsert=True)
            await self.update_nick(ctx.author, True)
            await ctx.reply(content="You are now AFK.", mention_author=False)
            return
        elif len(split) >= 2 and split[1] not in args:
            if str(ctx.author.id) in doc:
                await ctx.reply(content="You are already AFK.", mention_author=False)
                return
            reason = " ".join(split[1:])
            collection.update_one({"_id": f"afk.{ctx.guild.id}"}, {"$set": {f"{ctx.author.id}.reason": reason, f"{ctx.author.id}.time": int(datetime.now().timestamp())}}, upsert=True)
            await self.update_nick(ctx, True)
            await ctx.reply(content=f"I set your AFK to: {reason}", mention_author=False)
            return
        elif split[1] == "clear":
            if not ctx.author.guild_permissions.administrator:
                await ctx.reply(content="You do not have permission to use this command.", mention_author=False)
                return
            if len(split) != 3:
                await ctx.reply(content="Please provide a user to clear.", mention_author=False)
                return
            user = split[2]
            user = user.replace("<", "").replace("@", "").replace(">", "")
            collection.update_one({"_id": f"afk.{ctx.guild.id}"}, {"$unset": {f"{user}": ""}})
            cache = self.cache.get(str(ctx.guild.id))
            if not cache:
                cache = {}
            if user in cache:
                del cache[user]
            self.cache[str(ctx.guild.id)] = cache
            member = await ctx.guild.fetch_member(user)
            try:
                current_nick = member.nick
                new_nick = current_nick.replace("[AFK] ", "")
                await member.edit(nick=new_nick)
            except:
                return
            await ctx.reply(content=f"I cleared <@{user}>'s AFK.", mention_author=False)
            return
        elif split[1] == "ignore":
            if len(split) != 3:
                await ctx.reply(content="Please provide a channel to ignore or unignore.", mention_author=False)
                return
            channel = split[2]
            channel = channel.replace("<", "").replace("#", "").replace(">", "")
            channel = int(channel)
            cache = self.ignore_cache.get(str(ctx.author.id))
            if not cache:
                cache = []
            if channel in cache:
                collection.update_one({"_id": "afk_ignore"}, {"$pull": {f"{ctx.author.id}": channel}}, upsert=True)
                cache.remove(channel)
                await ctx.reply(content=f"I will no longer ignore <#{channel}>.", mention_author=False)
            else:
                collection.update_one({"_id": "afk_ignore"}, {"$push": {f"{ctx.author.id}": channel}}, upsert=True)
                cache.append(channel)
                await ctx.reply(content=f"I will now ignore <#{channel}>.", mention_author=False)
            self.ignore_cache[str(ctx.author.id)] = cache
            return
        elif split[1] == "ignored":
            doc = collection.find_one({"_id": f"afk_ignore"})
            if not doc:
                await ctx.reply(content="You are not ignoring any channels.", mention_author=False)
                return
            if str(ctx.author.id) not in doc:
                await ctx.reply(content="You are not ignoring any channels.", mention_author=False)
                return
            await ctx.reply(content=f"You are ignoring the following channels: {', '.join([f'<#{channel}>' for channel in doc[str(ctx.author.id)]])}", mention_author=False)
            return
        elif split[1] == "remove":
            cache = self.cache.get(str(ctx.guild.id))
            if not cache:
                cache = {}
            if str(ctx.author.id) in cache:
                del cache[str(ctx.author.id)]
            else:
                await ctx.reply(content="You are not AFK.", mention_author=False)
                return
            self.cache[str(ctx.guild.id)] = cache
            collection.update_one({"_id": f"afk.{ctx.guild.id}"}, {"$unset": {f"{ctx.author.id}": ""}})
            await ctx.reply(content="You are no longer AFK.", mention_author=False)
            return

    @nextcord.slash_command(name="afk", description="Manage your AFK status")
    @application_checks.guild_only()
    async def afk_command_slash(self, interaction: nextcord.Interaction):
        pass

    @afk_command_slash.subcommand(name="set", description="Set your AFK status")
    @application_checks.guild_only()
    async def afk_set(self, interaction: nextcord.Interaction, reason: str = None):
        doc = collection.find_one({"_id": f"afk.{interaction.guild.id}"})
        allowed = configuration.find_one({"_id": "config"})["afk"]
        if str(interaction.guild.id) not in allowed:
            allowed = []
        else:
            allowed = allowed[str(interaction.guild.id)]
        if not doc:
            doc = {}
        user_roles = [role.id for role in interaction.user.roles]
        if not any(role in allowed for role in user_roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if str(interaction.user.id) in doc:
            await interaction.response.send_message("You are already AFK.", ephemeral=True)
            return
        afk_reason = reason if reason else "AFK"
        collection.update_one({"_id": f"afk.{interaction.guild.id}"}, {"$set": {f"{interaction.user.id}.reason": afk_reason, f"{interaction.user.id}.time": int(datetime.now().timestamp())}}, upsert=True)
        await self.update_nick(interaction, True)
        await interaction.response.send_message(f"You are now AFK: {afk_reason}", ephemeral=True)

    @afk_command_slash.subcommand(name="clear", description="Clear a user's AFK status")
    @application_checks.guild_only()
    async def afk_clear_slash(self, interaction: nextcord.Interaction, target: nextcord.Member):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        user_id = str(target.id)
        collection.update_one({"_id": f"afk.{interaction.guild.id}"}, {"$unset": {f"{user_id}": ""}})
        cache = self.cache.get(str(interaction.guild.id))
        if not cache:
            cache = {}
        if user_id in cache:
            del cache[user_id]
        self.cache[str(interaction.guild.id)] = cache
        member = await interaction.guild.fetch_member(user_id)
        try:
            current_nick = member.nick
            new_nick = current_nick.replace("[AFK] ", "")
            await member.edit(nick=new_nick)
        except:
            return
        await interaction.response.send_message(f"I cleared {target.mention}'s AFK.", ephemeral=True)

    @afk_command_slash.subcommand(name="ignore", description="Ignore or unignore a channel for AFK checks")
    @application_checks.guild_only()
    async def afk_ignore_slash(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        allowed = configuration.find_one({"_id": "config"})["afk"]
        if str(interaction.guild.id) not in allowed:
            allowed = []
        else:
            allowed = allowed[str(interaction.guild.id)]
        user_roles = [role.id for role in interaction.user.roles]
        if not any(role in allowed for role in user_roles) and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        channel_id = channel.id
        cache = self.ignore_cache.get(str(interaction.user.id))
        if not cache:
            cache = []
        if channel_id in cache:
            collection.update_one({"_id": "afk_ignore"}, {"$pull": {f"{interaction.user.id}": channel_id}}, upsert=True)
            cache.remove(channel_id)
            await interaction.response.send_message(f"I will no longer ignore {channel.mention}.", ephemeral=True)
        else:
            collection.update_one({"_id": "afk_ignore"}, {"$push": {f"{interaction.user.id}": channel_id}}, upsert=True)
            cache.append(channel_id)
            await interaction.response.send_message(f"I will now ignore {channel.mention}.", ephemeral=True)
        self.ignore_cache[str(interaction.user.id)] = cache

    @afk_command_slash.subcommand(name="ignored", description="List ignored channels for AFK checks")
    @application_checks.guild_only()
    async def afk_ignored_slash(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": "afk_ignore"})
        if not doc or str(interaction.user.id) not in doc:
            await interaction.response.send_message("You are not ignoring any channels.", ephemeral=True)
            return
        ignored_channels = ', '.join([f'<#{channel}>' for channel in doc[str(interaction.user.id)]])
        await interaction.response.send_message(f"You are ignoring the following channels: {ignored_channels}", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        try:
            if message.author.bot:
                return
            if message.mentions:
                asyncio.create_task(self.afk_check_afk(message))
        except:
            return
        try:
            cache = self.cache.get(str(message.guild.id))
            if not cache:
                return
            if str(message.author.id) in cache:
                asyncio.create_task(self.afk_uncheck(message))
        except:
            return
        
    async def update_nick(self, message, bool):
        if bool:
            try:
                current_nick = message.author.nick
                if current_nick is None:
                    return
                new_nick = f"[AFK] {current_nick}"
                await message.author.edit(nick=new_nick)
            except:
                return
        else:
            try:
                current_nick = message.author.nick
                if current_nick is None:
                    return
                new_nick = current_nick.replace("[AFK] ", "")
                await message.author.edit(nick=new_nick)
            except:
                return

    async def afk_check_afk(self, message):
        cache = None
        try:
            cache = self.cache.get(str(message.guild.id))
        except:
            return
        ignored = self.ignore_cache
        if not cache:
            return
        for mention in message.mentions:
            if mention.id == message.author.id:
                continue
            user_ignored = ignored.get(str(mention.id))
            if not user_ignored:
                user_ignored = []
            if message.channel.id in user_ignored:
                continue
            if str(mention.id) in cache:
                afk_time = datetime.fromtimestamp(cache[str(mention.id)]['time'])
                time_diff = datetime.now() - afk_time
                seconds = time_diff.total_seconds()
                if seconds < 60:
                    time_ago = f"{int(seconds)} seconds ago"
                elif seconds < 3600:
                    time_ago = f"{int(seconds // 60)} minutes ago"
                elif seconds < 86400:
                    time_ago = f"{int(seconds // 3600)} hours ago"
                elif seconds < 604800:
                    time_ago = f"{int(seconds // 86400)} days ago"
                else:
                    time_ago = f"{int(seconds // 604800)} weeks ago"
                await message.reply(content=f"<@{mention.id}> is AFK: {cache[str(mention.id)]['reason']} - {time_ago}", allowed_mentions=nextcord.AllowedMentions(users=False, roles=False, everyone=False), mention_author=False)

    async def afk_uncheck(self, message):
        cache = self.cache.get(str(message.guild.id))
        ignored = self.ignore_cache.get(str(message.author.id))

        if not cache:
            return
        
        if not ignored:
            ignored = []

        if str(message.author.id) in cache and message.channel.id not in ignored:
            collection.update_one({"_id": f"afk.{message.guild.id}"}, {"$unset": {f"{message.author.id}": ""}})
            del cache[str(message.author.id)]
            self.cache[str(message.guild.id)] = cache
            msg = await message.reply(content=f"Welcome back {message.author.mention}! You are no longer AFK.")
            await self.update_nick(message, False)
            await asyncio.sleep(2)
            try:
                await msg.delete()
            except:
                return
            return
        
def setup(bot):
    bot.add_cog(AFK(bot))
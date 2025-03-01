from datetime import datetime
import aiohttp
import nextcord
import asyncio
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection
from nextcord.ext import tasks
import json

with open("config.json", "r") as file:
    config = json.load(file)

GREEN_CHECK = "<:green_check:1218286675508199434>"
RED_X = "<:red_x:1218287859963007057>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Highlight"]

class Highlight(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Highlight cog loaded")
        self.loop.start()
        self.lock = asyncio.Lock()
        self.update_cache.start()
    
    @tasks.loop(minutes=3)
    async def update_cache(self):
        for guild in self.bot.guilds:
            cache = collection.find_one({"_id": f"highlights.{guild.id}"})
            if cache:
                array = self.cache.get(guild.id)
                if not array:
                    array = []
                for key in cache.keys():
                    if key == "_id" or key == "recent" or key == "dm_times":
                        continue
                    try:
                        key = str(key)
                        array.append(key.lower())
                    except:
                        pass
                self.cache[guild.id] = array
            else:
                self.cache[guild.id] = []
                collection.insert_one({"_id": f"highlights.{guild.id}", "recent": {}, "dm_times": {}})

    @tasks.loop(minutes=30)
    async def loop(self):
        try:
            docs = list(collection.find({}))
            config = db["Configuration"]
            configuration = config.find_one({"_id": "config"})["highlight"]
            for doc in docs:
                if "highlights" not in doc["_id"]:
                    continue
                guild = doc["_id"].split(".")[1]
                try:
                    doc.pop("_id")
                    doc.pop("recent") 
                    doc.pop("dm_times")
                except:
                    pass
                guild = str(guild)
                if guild not in configuration:
                    continue
                access_roles = configuration[guild]
                guild = int(guild)
                guild_id = guild
                for key in doc.keys():
                    owners = doc[key]
                    owners_to_keep = []
                    for owner in owners:
                        try:
                            guild = self.bot.get_guild(guild_id)
                            member = guild.get_member(int(owner))
                        except:
                            continue
                        if not member:
                            continue
                        member_roles = [role.id for role in member.roles]
                        should_remove = True
                        for role in member_roles:
                            if role in access_roles:
                                should_remove = False
                                break
                        if not should_remove:
                            owners_to_keep.append(owner)
                    
                    if not owners_to_keep:
                        collection.update_one({"_id": f"highlights.{guild_id}"}, {"$unset": {key: ""}})
                    else:
                        collection.update_one({"_id": f"highlights.{guild_id}"}, {"$set": {key: owners_to_keep}})
        except Exception as e:
            print(f"Error in highlight loop: {e}")

        
    @commands.command(name="highlight", aliases=["hl"], description="Enable or disable highlighting")
    async def highlight(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            await self.highlight_help(ctx)
            return 
        user_roles = [role.id for role in ctx.author.roles]
        config = db["Configuration"]
        doc = config.find_one({"_id": "config"})
        allowed = doc["highlight"]
        guild = str(ctx.guild.id)
        doc2 = collection.find_one({"_id": f"highlights.{guild}"})
        doc3 = collection.find_one({"_id": f"blacklists.{guild}"})
        if not doc2:
            collection.insert_one({"_id": f"highlights.{guild}", "recent": {}, "dm_times": {}})
        if not doc3:
            collection.insert_one({"_id": f"blacklists.{guild}"})
        if guild not in allowed:
            await ctx.message.add_reaction(RED_X)
            return
        else:
            if not any(role in allowed[guild] for role in user_roles):
                await ctx.message.add_reaction(RED_X)
                return
        args = ["clear", "list", "clr", "remove", "blacklist"]
        if split[1] in args:
            if split[1] == "clear" or split[1] == "clr":
                await self.clear(ctx)
            elif split[1] == "remove":
                await self.remove(ctx)
            elif split[1] == "blacklist":
                await self.blacklist(ctx)
            else:
                await self.list(ctx)
        else:
            await self.add_highlight(ctx)

    async def blacklist(self, ctx):
        msg = ctx.message.content
        msg = msg.replace("hl blacklist", "")
        msg = msg.replace("highlight blacklist", "")
        msg = msg.replace("!", "").replace(".", "").replace("-", "")
        msg = msg.replace("<", "").replace("@", "").replace(">", "")
        msg = int(msg)
        try:
            auth = await self.bot.fetch_user(msg)
        except:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("Invalid user.", mention_author=False)
            return
        doc = collection.find_one({"_id": f"blacklists.{ctx.guild.id}"})
        if str(ctx.author.id) in doc:
            more = doc[str(ctx.author.id)]
            if msg in more:
                collection.update_one({"_id": f"blacklists.{ctx.guild.id}"}, {"$pull": {f"{ctx.author.id}": msg}}, upsert=True)
                await ctx.reply(f"Removed user {msg} ({auth.name}) from your blacklist.", mention_author=False)
        else:
            collection.update_one({"_id": f"blacklists.{ctx.guild.id}"}, {"$push": {f"{ctx.author.id}": msg}}, upsert=True)
            await ctx.reply(f"Blacklisted user {msg} ({auth.name}).", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        
    async def highlight_help(self, ctx):
        descp = f"This embed will help guide you to understand how to use the higlight command. You can trigger this command with `!hl` or `!highlight`. The subcommands that are supproted are listed below. Correct syntax is `!hl <subcommand> [arguments]`. \n\nThis command is currently in beta. If you would like to learn more about it and participate in the beta, please contact the bot owner."
        embed = nextcord.Embed(title="Highlight Command", description=descp, color=nextcord.Color.blurple())
        embed.add_field(name="add", value="To add a word to your highlights, do `!hl <word>`. There is no need to add the ""add"" argument to the command.", inline=False)
        embed.add_field(name="remove", value="Remove a word from your highlights. Correct syntax is `!hl remove <word>`.", inline=False)
        embed.add_field(name="clear", value="Clear all your highlighted words. Correct syntax is `!hl clear`.", inline=False)
        embed.add_field(name="list", value="List all your highlighted words. Correct syntax is `!hl list`.", inline=False)
        embed.add_field(name="blacklist", value="Blacklist a user from being highlighted. Correct syntax is `!hl blacklist <user id/mention>`. This will prevent the user from being highlighted even if they trigger a highlighted word. If they are already blacklisted, they will be removed from the blacklist.", inline=False)
        await ctx.reply(embed=embed, mention_author=False)

    async def add_highlight(self, ctx):
        doc = collection.find_one({"_id": f"highlights.{ctx.guild.id}"})
        try:
            doc.pop("_id")
            doc.pop("recent")
            doc.pop("dm_times")
        except:
            pass
        split = ctx.message.content.split(" ")
        if len(split) > 2:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("The word to highlight must be one word.", mention_author=False)
            return
        
        user_highlight_count = 0
        for value in doc.values():
            if isinstance(value, list) and ctx.author.id in value:
                user_highlight_count += 1
                
        if user_highlight_count >= 10:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You cannot highlight more than 10 words.", mention_author=False)
            return
            
        word = split[1]
        if word in doc:
            users = doc[word]
            if ctx.author.id in users:
                await ctx.message.add_reaction(RED_X)
                await ctx.reply(f"You already have `{word}` highlighted.", mention_author=False)
                return
        collection.update_one({"_id": f"highlights.{ctx.guild.id}"}, {"$push": {word: ctx.author.id}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Added `{word}` to your highlights.", mention_author=False)

    async def clear(self, ctx):
        doc = collection.find_one({"_id": f"highlights.{ctx.guild.id}"})
        try:
            doc.pop("_id")
            doc.pop("recent")
            doc.pop("dm_times")
        except:
            pass
        for item, value in doc.items():
            if isinstance(value, list):
                if ctx.author.id in value:
                    value.remove(ctx.author.id)
                    collection.update_one({"_id": f"highlights.{ctx.guild.id}"}, {"$set": {item: value}})
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply("Cleared all your highlighted words.", mention_author=False)

    async def list(self, ctx):
        doc = collection.find_one({"_id": f"highlights.{ctx.guild.id}"})
        try:
            doc.pop("_id")
            doc.pop("recent")
            doc.pop("dm_times")
        except:
            pass
        descp = ""
        for item, value in doc.items():
            if isinstance(value, list) and ctx.author.id in value:
                descp = f"{descp}\n`{item}`"
        
        if descp == "":
            await ctx.reply("You have no highlighted words.", mention_author=False)
            return
            
        embed = nextcord.Embed(title="Highlighted Words", description=f"{descp}", color=nextcord.Color.blurple())
        await ctx.reply(embed=embed, mention_author=False)

    async def remove(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) > 3:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("The word to remove must be one word.", mention_author=False)
            return
        word = split[2]
        doc = collection.find_one({"_id": f"highlights.{ctx.guild.id}"})
        current = doc[word] if word in doc else []
        if len(current) == 0:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply(f"You do not have `{word}` highlighted.", mention_author=False)
            return
        elif ctx.author.id not in current:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply(f"You do not have `{word}` highlighted.", mention_author=False)
            return
        collection.update_one({"_id": f"highlights.{ctx.guild.id}"}, {"$pull": {word: ctx.author.id}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Removed `{word}` from your highlights.", mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if isinstance(message.channel, nextcord.DMChannel) or message.author.bot:
            return
        words = self.cache.get(message.guild.id)
        if not words:
            return
        for word in words:
            if word in message.content.lower():
                asyncio.create_task(self.highlighter(message))
                break
        asyncio.create_task(self.update_user_cache(message))

    async def update_user_cache(self, message: nextcord.Message):
        collection.update_one({"_id": f"highlights.{message.guild.id}"}, {"$set": {f"recent.{message.author.id}": int(message.created_at.timestamp())}}, upsert=True)
        
    async def highlighter(self, message: nextcord.Message):
        highlights = collection.find_one({"_id": f"highlights.{message.guild.id}"})
        if not highlights:
            return

        times = highlights.get("recent", {})
        dm_times = highlights.get("dm_times", {})
        current_time = int(datetime.now().timestamp())
        message_time = int(message.created_at.timestamp())
        owner_words = {}
        msg_content_lower = message.content.lower()

        highlights.pop("_id")
        highlights.pop("recent")
        highlights.pop("dm_times")
        
        for item, users in highlights.items():
            if not isinstance(users, list) or item in ['_id', 'recent', 'dm_times']:
                continue
            if message.author.id in users:
                continue
            if item.lower() in msg_content_lower:
                for owner in users:
                    if str(owner) in times and message_time - times[str(owner)] < 180:
                        continue
                    if str(owner) in dm_times and current_time - dm_times[str(owner)] < 120:
                        continue
                    owner_words.setdefault(owner, []).append(item)

        if not owner_words:
            return

        messages = []
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://google.com") as response:
                    if response.status == 200:
                        try:
                            async with asyncio.timeout(180):
                                async for msg in message.channel.history(limit=5, before=message):
                                    try:
                                        messages.append(f"\n**{msg.author.name}:** {msg.content}")
                                    except:
                                        continue
                        except asyncio.TimeoutError:
                            messages = ["**Unable to find Context**"]
        except Exception:
            messages = ["**Unable to find Context**"]

        messages.append(f"\n**{message.author.name}:** {message.content}")
        context = "".join(messages)

        blacklist_doc = collection.find_one(
            {"_id": f"blacklists.{message.guild.id}"},
            {"_id": 0}
        )

        embed = nextcord.Embed(
            title="Context:", 
            description=context, 
            color=nextcord.Color.blurple()
        )
        embed.add_field(name="Jump", value=f"[Jump to Message]({message.jump_url})")
        embed.timestamp = message.created_at
        
        for owner, triggered_words in owner_words.items():
            member = message.guild.get_member(int(owner))
            if not member or member not in message.channel.members:
                continue
            if blacklist_doc and str(owner) in blacklist_doc and message.author.id in blacklist_doc[str(owner)]:
                continue

            words_list = ", ".join(f"`{word}`" for word in triggered_words)
            content = f"{message.author.mention} ({message.author.name}) referenced your highlighted words {words_list} in <#{message.channel.id}>"
            
            try:
                async with self.lock:
                    await member.send(content=content, embed=embed)
                    collection.update_one(
                        {"_id": f"highlights.{message.guild.id}"}, 
                        {"$set": {f"dm_times.{owner}": message_time}},
                        upsert=True
                    )
            except:
                continue

def setup(bot):
    bot.add_cog(Highlight(bot))
import asyncio
import nextcord
from nextcord.ext import commands, tasks
import random
from datetime import datetime, timedelta

fivehundred = 1386481737478967296
billion = 1386481804105748620

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Fun Commands"]
acollection = db["Admin"]
configuration = db["Configuration"]

class FunCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}
        try:
            self.deleted_messages = collection.find_one({"_id": "snipe_messages"})["messages"]
        except:
            self.deleted_messages = {}
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Fun Commands cog is ready")
        if self.log_snipes.is_running():
            pass
        else:
            await self.log_snipes.start()

    @tasks.loop(minutes=1)
    async def log_snipes(self):
        collection.update_one({"_id": "snipe_messages"}, {"$set": {"messages": self.deleted_messages}}, upsert=True)
       
    @commands.command(name="snipe")
    async def snipe(self, ctx: commands.Context):
        doc = configuration.find_one({"_id": "config"})
        snipe = doc["perks"]["snipe"]
        snipe_roles = snipe.get(str(ctx.guild.id), "None")
        user_roles = [role.id for role in ctx.author.roles]
        if snipe_roles == "None" and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("Snipe is not enabled for this server.", mention_author=False)
            return
        elif not any(role in snipe_roles for role in user_roles) and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return

        split = ctx.message.content.split(" ")
        if len(split) < 2:
            channel = ctx.channel
            split_index = 1
        else:
            if "<#" in split[1]:
                channel = split[1]
                channel = channel.replace("<", "").replace("#", "").replace(">", "")
                channel = ctx.guild.get_channel(int(channel))
                if len(split) < 3:
                    split_index = 1
                else:
                    try:
                        split_index = int(split[2])
                    except:
                        await ctx.reply("Please specify a message number between 1 and 5 (e.g. `!snipe #channel 2`).", mention_author=False)
                        return
            else:
                channel = ctx.channel
                try:
                    split_index = int(split[1])
                except:
                    await ctx.reply("Please specify a message number between 1 and 5 (e.g. `!snipe 2`).", mention_author=False)
                    return

        if ctx.author not in channel.members:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You cannot snipe in this channel.", mention_author=False)
            return
        if str(channel.id) not in self.deleted_messages or not self.deleted_messages[str(channel.id)]:
            await ctx.message.add_reaction(RED_X)
            if ctx.channel.id == channel.id:
                await ctx.reply("There are no recently deleted messages in this channel.", mention_author=False)
            else:
                await ctx.reply("There are no recently deleted messages in that channel.", mention_author=False)
            return

        messages = self.deleted_messages[str(channel.id)]
        if len(messages) < split_index:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("There are not that many deleted messages in this channel. You can only snipe the last 5 deleted messages.", mention_author=False)
            return

        message_data = messages[-split_index]
        author = self.bot.get_user(message_data["author_id"])
        embed = nextcord.Embed(description=f"{message_data['content']} (<t:{message_data['timestamp']}:R>)", color=0x3498db)
        embed.timestamp = datetime.now()
        if author is not None:
            embed.set_author(name=f"{author.name} ({author.id})", icon_url=author.display_avatar.url)
        else:
            embed.set_author(name=f"Unknown ({message_data['author_id']})")
        embed.set_footer(text=f"Sniped by {ctx.author.name} • Message #{split_index}")
        await ctx.reply(embed=embed, mention_author=False)

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
        cooldowns = self.cooldowns
        if ctx.author.id in cooldowns:
            if cooldowns[ctx.author.id] + 15 > int(datetime.now().timestamp()):
                await ctx.reply(f"You are on cooldown, you can use this command again <t:{cooldowns[ctx.author.id] + 15}:R>", mention_author=False)
                await ctx.message.add_reaction(RED_X)
                return
        bot_admins = acollection.find_one({"_id": "bot_admins"})
        roles = [role.id for role in ctx.author.roles]
        access_roles = [1386481965578063882]
        if not ctx.author.guild_permissions.administrator and ctx.author.id not in bot_admins["admins"] and not any(role in access_roles for role in roles):
            await ctx.message.add_reaction(RED_X)
            return
        
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            await ctx.message.add_reaction(RED_X)
            return
        
        message = split[1]
        message = message.replace("<", "").replace("@", "").replace(">", "")
        message = int(message)
        cooldowns[ctx.author.id] = int(datetime.now().timestamp())
        user = self.bot.get_user(message)
        if user is None:
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await asyncio.sleep(2)
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")
        await ctx.channel.send(f"{user.mention}")

    @commands.Cog.listener()
    async def on_message_delete(self, message: nextcord.Message):
        if not message.content or message.content == "":
            return
        channel_id = str(message.channel.id)
        msg_data = {
            "content": message.content,
            "author_id": message.author.id,
            "timestamp": int(datetime.now().timestamp())
        }
        if channel_id not in self.deleted_messages or not isinstance(self.deleted_messages[channel_id], list):
            self.deleted_messages[channel_id] = []
        self.deleted_messages[channel_id].append(msg_data)
        self.deleted_messages[channel_id] = self.deleted_messages[channel_id][-5:]

def setup(bot):
    bot.add_cog(FunCommands(bot))





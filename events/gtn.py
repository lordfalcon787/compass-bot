import nextcord
from nextcord.ext import commands, tasks
import random
import asyncio
from utils.mongo_connection import MongoConnection

EMAN = 1205270486469058637
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
ARROW_UP = "<:arrow_up:1227876663069638678>"
ARROW_DOWN = "<:arrow_down:1227877135423897623>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["GTN"]
misc = db["Misc"]
configuration = db["Configuration"]

class Gtn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.gtn_lock = asyncio.Lock()
        self.cache = {}

    def cog_unload(self):
        if self.rc_gtn.is_running():
            self.rc_gtn.cancel()
        if self.cache_update.is_running():
            self.cache_update.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Guess the number cog loaded.")
        if not self.rc_gtn.is_running():
            self.rc_gtn.start()
        if not self.cache_update.is_running():
            self.cache_update.start()

    @tasks.loop(seconds=30)
    async def cache_update(self):
        self.cache = {}
        docs = list(collection.find({}))
        for doc in docs:
            self.cache[doc["_id"]] = doc["number"]

    @tasks.loop(minutes=3)
    async def rc_gtn(self):
        if collection.find_one({"_id": 1224120097929691237}):
            return
        guild = self.bot.get_guild(1205270486230110330)
        channel = guild.get_channel(1224120097929691237)
        ranges = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 2000]
        range = random.choice(ranges)
        rand = random.randint(1, range)
        embed = nextcord.Embed(title="Game Started", description=f"Guess the number between 1 and {range}.", color=8421504)
        embed.set_footer(text=f"First to guess the correct number wins.")
        await channel.send(embed=embed)
        self.cache[channel.id] = rand
        collection.insert_one({"_id": channel.id, "number": rand})
        await channel.edit(slowmode_delay=1)
        
    @commands.command(name="gtn")
    async def gtn(self, ctx):
        roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})["event_manager_role"]
        guild = str(ctx.guild.id)
        if guild not in config:
            if not ctx.author.guild_permissions.manage_messages:
                await ctx.message.add_reaction(RED_X)
                return
        else:
            if not ctx.author.guild_permissions.administrator and config[guild] not in roles:
                await ctx.message.add_reaction(RED_X)
                return
        
        number = ctx.message.content.split(" ")[1]
        if number == "end":
            if collection.find_one({"_id": ctx.channel.id}):
                number = collection.find_one({"_id": ctx.channel.id})["number"]
                collection.delete_one({"_id": ctx.channel.id})
                self.cache.pop(ctx.channel.id)
                embed = nextcord.Embed(title="Game Ended", description=f"The game has been ended. The number was {number}.", color=65280)
                embed.set_footer(text=f"Thank you all for playing.", icon_url=ctx.author.avatar.url)
                await ctx.send(embed=embed)
                return
            else:
                await ctx.message.add_reaction(RED_X)
                return

        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        quantity = number.lower()
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(quantity[:-1])
                multiplier = multipliers[quantity[-1]]
                quantity = int(numeric_part * multiplier)
            except ValueError:
                await ctx.message.add_reaction(RED_X)
                return
        else:
            if ',' in quantity:
                quantity = quantity.replace(',', '')
            try:
                quantity = int(quantity)
            except ValueError:
                await ctx.message.add_reaction(RED_X)
                return
            
        if quantity < 2:
            await ctx.message.add_reaction(RED_X)
            return

        if collection.find_one({"_id": ctx.channel.id}):
            await ctx.message.add_reaction(RED_X)
            return
        rand = random.randint(1, quantity)
        embed = nextcord.Embed(title="Game Started", description=f"Guess the number between 1 and {quantity}.", color=8421504)
        embed.set_footer(text=f"First to guess the correct number wins.")
        self.cache[ctx.channel.id] = rand
        collection.insert_one({"_id": ctx.channel.id, "number": rand})
        await ctx.send(embed=embed)
        await ctx.channel.edit(slowmode_delay=2)
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.author.send(f"The number is {rand}.")

    @nextcord.slash_command(name="gtn")
    async def gtn_slash(self, interaction):
        pass

    @gtn_slash.subcommand(name="arrowexempt", description="Exempt a channel from arrows.")
    async def gtn_slash_exempt(self, interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"{RED_X} You do not have permission to use this command.", ephemeral=True)
            return
        arrow_exempt = misc.find_one({"_id": "arrow_exempt"})
        if arrow_exempt:
            arrow_exempt = arrow_exempt.get(str(interaction.guild.id), [])
        else:
            arrow_exempt = []
        if channel.id in arrow_exempt:
            arrow_exempt.remove(channel.id)
            misc.update_one({"_id": "arrow_exempt"}, {"$set": {str(interaction.guild.id): arrow_exempt}}, upsert=True)
            await interaction.response.send_message(f"{GREEN_CHECK} Channel removed from arrow exempt list.", ephemeral=True)
        else:
            arrow_exempt.append(channel.id)
            misc.update_one({"_id": "arrow_exempt"}, {"$set": {str(interaction.guild.id): arrow_exempt}}, upsert=True)
            await interaction.response.send_message(f"{GREEN_CHECK} Channel exempted from arrows.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.content.isdigit():
            return
        number = self.cache.get(message.channel.id)
        if not number:
            return
            
        async with self.gtn_lock:
            guess = int(message.content)
            if guess == number:
                await asyncio.gather(
                    message.add_reaction(GREEN_CHECK),
                    self.gtn_win(message)
                )
                return 
            arrow_exempt = misc.find_one({"_id": "arrow_exempt"})
            if arrow_exempt:
                arrow_exempt = arrow_exempt.get(str(message.guild.id), [])
            else:
                arrow_exempt = []
            if message.channel.id in arrow_exempt:
                if guess != number:
                    asyncio.create_task(self.red_x(message))
                return
            if random.randint(1, 100) <= 10:
                if guess < number:
                    await message.add_reaction(ARROW_UP)
                else:
                    await message.add_reaction(ARROW_DOWN)
            else:
                await message.add_reaction(RED_X)

    async def red_x(self, message):
        await message.add_reaction(RED_X)

    async def gtn_win(self, message):
        number = self.cache.get(message.channel.id, None)
        if not number:
            return
        self.cache.pop(message.channel.id)
        collection.delete_one({"_id": message.channel.id})
        embed = nextcord.Embed(title="Game Ended", description=f"{message.author.mention} guessed the number! The number was {number}.", color=65280)
        embed.set_footer(text=f"Thank you all for playing.", icon_url=message.author.avatar.url)
        await message.reply(embed=embed)
        await message.channel.edit(slowmode_delay=None)

def setup(bot):
    bot.add_cog(Gtn(bot))
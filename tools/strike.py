import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

GREEN_CHECK = "<:green_check:1218286675508199434>"
RED_X = "<:red_x:1218287859963007057>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Strikes"]
configuration = db["Configuration"]

class Strike(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Strike cog loaded.")

    async def remove_strike(self, ctx):
        try:
            if not ctx.author.guild_permissions.administrator:
                await ctx.message.add_reaction(RED_X)
                return
            args = ctx.message.content.split(" ")
            if len(args) < 4:
                await ctx.message.add_reaction(RED_X)
                return
            user = args[2]
            user = user.replace("<@", "").replace(">", "")
            user = int(user)
            strike_num = args[3]
            doc = collection.find_one({"_id": f"strikes_{ctx.guild.id}"})
            if not doc or str(user) not in doc:
                await ctx.message.add_reaction(RED_X)
                await ctx.reply("This user has no strikes.", mention_author=False)
                return
            
            if strike_num not in doc[str(user)]:
                await ctx.message.add_reaction(RED_X)
                await ctx.reply("This strike does not exist.", mention_author=False)
                return
            del doc[str(user)][str(strike_num)]
            collection.update_one({"_id": f"strikes_{ctx.guild.id}"}, {"$set": doc})
            await ctx.message.add_reaction(GREEN_CHECK)
        except Exception as e:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply(f"An error occurred: {str(e)}", mention_author=False)

    @commands.command(name="strikes")
    async def display_strikes(self, ctx):
        user = ctx.author
        if ctx.author.guild_permissions.administrator and len(ctx.message.content.split(" ")) > 1:
            user = ctx.message.content.split(" ")[1]
            user = user.replace("<@", "").replace(">", "").replace("!", "")
            try:
                user = await self.bot.fetch_user(user)
            except:
                await ctx.message.add_reaction(RED_X)
                return
        doc = collection.find_one({"_id": f"strikes_{ctx.guild.id}"})
        if not doc or str(user.id) not in doc:
            embed = nextcord.Embed(title=f"{user.name}'s Strikes", description=f"This user has no strikes.", color=16711680)
            await ctx.reply(embed=embed, mention_author=False)
            return
        embed = nextcord.Embed(title=f"{user.name}'s Strikes", color=65280)
        num = 1
        for strike in doc[str(user.id)]:
            try:
                value = doc[str(user.id)][str(num)]
            except:
                break
            embed.add_field(name=f"Strike #{num}", value=f"`{value}`", inline=False)
            num = num + 1
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="strike")
    async def strike_handler(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        args = ctx.message.content.split(" ")
        if len(args) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        user = args[1]

        if user.lower() == "remove":
            await self.remove_strike(ctx)
            return

        reason = " ".join(args[2:])

        user = user.replace("<@", "").replace(">", "").replace("!", "")
        user = int(user)
        try:
            user = await self.bot.fetch_user(user)
        except:
            await ctx.message.add_reaction(RED_X)
            return
        
        doc = collection.find_one({"_id": f"strikes_{ctx.guild.id}"})
        strike_num = 0
        if not doc:
            strike_num = 1
        else:
            if str(user.id) in doc:
                strike_num = len(doc[str(user.id)]) + 1
            else:
                strike_num = 1
        
        collection.update_one({"_id": f"strikes_{ctx.guild.id}"}, {"$set": {f"{user.id}.{strike_num}": reason}}, upsert=True)
        guild = str(ctx.guild.id)
        embed = nextcord.Embed(title=f"Strike #{strike_num}", description=f"{user.mention} has received a strike for: {reason}", color=65280)
        config = configuration.find_one({"_id": f"config"})
        if guild not in config["strike_log"]:
            pass
        else:
            await self.bot.get_channel(config["strike_log"][guild]).send(embed=embed)
        if guild not in config["strike_announce"]:
            pass
        else:
            await self.bot.get_channel(config["strike_announce"][guild]).send(content=f"{user.mention}", embed=embed)
        await ctx.message.add_reaction(GREEN_CHECK)

def setup(bot):
    bot.add_cog(Strike(bot))

        
        
        
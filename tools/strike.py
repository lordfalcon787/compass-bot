import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection
from datetime import datetime, timezone

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

    @commands.command(name="fixstrikes")
    async def fix_strikes_command(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        await self.fix_strikes(ctx.guild.id)
        await ctx.message.add_reaction(GREEN_CHECK)

    async def fix_strikes(self, guild_id):
        doc = collection.find_one({"_id": f"strikes_{guild_id}"})
        updated = False
        if doc:
            for user_id in list(doc.keys()):
                if user_id == "_id":
                    continue
                user_strikes = doc[user_id]
                if isinstance(user_strikes, dict):
                    sorted_strikes = sorted(user_strikes.items(), key=lambda x: int(x[0]))
                    new_strikes = {}
                    for idx, (_, value) in enumerate(sorted_strikes, start=1):
                        if isinstance(value, dict) and "reason" in value and "date" in value:
                            new_strikes[str(idx)] = {
                                "reason": value["reason"],
                                "date": value["date"]
                            }
                        else:
                            new_strikes[str(idx)] = value
                    if list(user_strikes.values()) != list(new_strikes.values()) or list(user_strikes.keys()) != list(new_strikes.keys()):
                        doc[user_id] = new_strikes
                        updated = True
            if updated:
                collection.update_one({"_id": f"strikes_{guild_id}"}, {"$set": doc})

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
            await self.fix_strikes(ctx.guild.id)
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
            if isinstance(value, dict):
                timestamp = int(value['date'])
                embed.add_field(
                    name=f"Strike #{num}",
                    value=f"**Reason:** `{value['reason']}`\n**Date:** <t:{timestamp}:F>",
                    inline=False
                )
            else:
                embed.add_field(name=f"Strike #{num}", value=f"**Reason:** `{value}`", inline=False)
            num = num + 1
        if num == 1:
            embed.description = "This user has no strikes."
            embed.color = 16711680
            collection.update_one({"_id": f"strikes_{ctx.guild.id}"}, {"$unset": {f"{user.id}": ""}})
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
        
        if user.lower() == "clear":
            await self.clear_strikes(ctx)
            return

        reason = " ".join(args[2:])

        user = user.replace("<@", "").replace(">", "").replace("!", "")
        user = int(user)
        try:
            user = await self.bot.fetch_user(user)
        except:
            await ctx.message.add_reaction(RED_X)
            return
        await self.fix_strikes(ctx.guild.id)
        doc = collection.find_one({"_id": f"strikes_{ctx.guild.id}"})
        strike_num = 0
        if not doc:
            strike_num = 1
        else:
            if str(user.id) in doc:
                strike_num = len(doc[str(user.id)]) + 1
            else:
                strike_num = 1
        
        strike_data = {
            "reason": reason,
            "date": int(datetime.now().timestamp())
        }
        collection.update_one(
            {"_id": f"strikes_{ctx.guild.id}"},
            {"$set": {f"{user.id}.{strike_num}": strike_data}},
            upsert=True
        )
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

    async def clear_strikes(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        user = split[2]
        user = user.replace("<@", "").replace(">", "").replace("!", "")
        user = int(user)
        collection.update_one({"_id": f"strikes_{ctx.guild.id}"}, {"$unset": {f"{user}": ""}})
        await ctx.message.add_reaction(GREEN_CHECK)

def setup(bot):
    bot.add_cog(Strike(bot))

        
        
        
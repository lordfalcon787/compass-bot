import nextcord
import random
import asyncio
from datetime import datetime
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Currency"]

c = "⏣"
dice_1 = "<:dice1:1329530569260011580>"
dice_2 = "<:dice2:1329530573223497748>"
dice_3 = "<:dice3:1329530571868733542>"
dice_4 = "<:dice4:1329530568207237203>"
dice_5 = "<:dice5:1329530566546292828>"
dice_6 = "<:dice6:1329530570748858421>"
RC_ID = 1205270486230110330
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
HEADS = "https://upload.wikimedia.org/wikipedia/commons/a/a0/2006_Quarter_Proof.png"
TAILS = "https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/dc61c80b-e2ae-4da0-801e-4c84d7cf91b7/dc7egby-23b23f3b-db59-4e3e-b57f-8b1ada105126.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcL2RjNjFjODBiLWUyYWUtNGRhMC04MDFlLTRjODRkN2NmOTFiN1wvZGM3ZWdieS0yM2IyM2YzYi1kYjU5LTRlM2UtYjU3Zi04YjFhZGExMDUxMjYucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.QemscS80d_Q7Ir-sDQ26ZAiiTHIJHbRAzTgpW1tDvsw"

class View(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class Currency(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = []
        self.cooldown = {}
        self.se_cooldown = {}
        self.gr_cooldown = {}
        self.rt_cooldown = {}
        self.cf_cooldown = {}
        self.rob_cooldown = {}
        self.user_rob_cooldown = {}

    @tasks.loop(seconds=20)
    async def update_cache(self):
        self.cache = [doc["_id"] for doc in collection.find({})]

    def cog_unload(self):
        if self.update_cache.is_running():
            self.update_cache.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Currency cog loaded.")
        if not self.update_cache.is_running():
            self.update_cache.start()

    async def get_quantity(self, quantity):
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(quantity[:-1])
                multiplier = multipliers[quantity[-1]]
                quantity = int(numeric_part * multiplier)
            except ValueError:
                return None
        else:
            if ',' in quantity:
                quantity = quantity.replace(',', '')
            try:
                quantity = int(quantity)
            except ValueError:
                return None
        return quantity
    
    async def update_xp(self, ctx):
        doc = collection.find_one({"_id": ctx.author.id})
        xp = doc["xp"]
        xp += 5
        level = doc["level"]
        if xp >= 100:
            xp = abs(100 - xp)
            level += 1
        collection.update_one({"_id": ctx.author.id}, {"$set": {"xp": xp, "level": level}})

    async def update_coins(self, message):
        if message.channel.id == 1265160374534275124:
            return
        collection.update_one({"_id": message.author.id}, {"$inc": {"balance": 10000}})

    async def check_ban(self, ctx):
        doc = collection.find_one({"_id": ctx.author.id})
        if doc is None:
            return False
        if "banned" not in doc:
            return False
        embed = nextcord.Embed(title="Currency Banned", description=f"You are banned from the currency system until <t:{doc['banned']}:f> for `{doc['ban_reason']}`", color=nextcord.Color.red())
        embed.set_footer(text="This is a temporary ban and will be lifted when the time is up.", icon_url=ctx.guild.icon.url)
        if doc["banned"] > int(datetime.now().timestamp()):
            await ctx.reply(embed=embed, mention_author=False)
            return True
        return False

    async def check_channel(self, ctx):
        if ctx.channel.id == 1205270487274496054 and not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return True
        return False

    @commands.command(name="cban")
    async def cban(self, ctx, user: nextcord.Member, duration: str):
        if ctx.guild.id != RC_ID:
            return
        if ctx.author.id != 1166134423146729563:
            return
        if await self.check_channel(ctx):
            return
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.reply("Please provide a user and reason.", mention_author=False)
            return
        reason = " ".join(split[3:])
        time = int(datetime.now().timestamp())
        total_seconds = 0
        if "d" in duration:
            total_seconds += int(duration.split("d")[0]) * 86400
        elif "h" in duration:
            total_seconds += int(duration.split("h")[0]) * 3600
        elif "m" in duration:
            total_seconds += int(duration.split("m")[0]) * 60
        elif "s" in duration:
            total_seconds += int(duration.split("s")[0])
        if total_seconds == 0:
            await ctx.reply("Please provide a valid duration.", mention_author=False)
            return
        end_time = time + total_seconds
        collection.update_one({"_id": user.id}, {"$set": {"banned": end_time, "ban_reason": reason}})
        await ctx.message.add_reaction(GREEN_CHECK)
        await user.send(f"You have been banned from the currency system until <t:{end_time}:R> for `{reason}`.")
    @commands.command(name="cunban")
    async def cunban(self, ctx, user: nextcord.Member):
        if ctx.guild.id != RC_ID:
            return
        if ctx.author.id != 1166134423146729563:
            return
        if await self.check_channel(ctx):
            return
        collection.update_one({"_id": user.id}, {"$unset": {"banned": "", "ban_reason": ""}})
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="optin", aliases=["oi"])
    async def optin(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        data = collection.find_one({"_id": ctx.author.id})
        if data:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply("You are already opted in!", mention_author=False)
            return
        self.cache.append(ctx.author.id)
        collection.insert_one({"_id": ctx.author.id, "balance": 1000000, "bank": 0, "level": 1, "xp": 0, "net": 1000000, "passive": "False", "passive_cooldown": 0})
        await ctx.reply("You have opted in to the currency system!", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="optout", aliases=["oo"])
    async def optout(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        collection.delete_one({"_id": ctx.author.id})
        await ctx.reply("You have opted out of the currency system!", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="chelp")
    async def currencyhelp(self, ctx):
        if await self.check_channel(ctx):
            return
        embed = nextcord.Embed(title="Currency System Help", color=nextcord.Color.blurple())
        descp = "__**Main Commands:**__\n\n`!balance` - Check your balance, level, xp, and passive status.\n`!leaderboard` - Check the server leaderboard.\n`!passive [choice]` - Set your passive mode to True or False.\n`!adminset [user] [quantity]` - Set a user's balance to a quantity.\n`!admindelete [user]` - Delete a user's data.\n\n__**Game Commands:**__\n\n`!snakeeyes [quantity]` - Get two of the same dice and win.\n`!roulette [quantity] [choice]` - Predict the color, green has higher payout but lower appearance.\n`!coinflip [quantity] [choice]` - Flip a coin and gamble.\n`!gambleroll` - Roll a dice and gamble, you will most likely win.\n`!rob [user]` - Rob a user.\n`!give [user] [quantity]` - Give a user a quantity of currency.\n\n__**Other Commands:**__\n\n`!optin` - Opt in to the currency system.\n`!chelp` - Check the currency system help.\n`!optout` - Opt out of the currency system."
        embed.description = descp
        embed.set_thumbnail(url=ctx.guild.icon.url)
        embed.set_footer(text="Built by _lordfalcon_", icon_url=self.bot.user.avatar.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="passive")
    async def passive(self, ctx, choice: str):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        if await self.check_ban(ctx):
            return
        true = ["true", "t", "on", "1"]
        false = ["false", "f", "off", "0"]
        if choice.lower() in true:
            choice = "True"
        elif choice.lower() in false:
            choice = "False"
        else:
            await ctx.reply("Please enter a valid choice.", mention_author=False)
            return
        current = doc["passive"]
        if current == choice:
            await ctx.reply("You are already in that passive mode!", mention_author=False)
            return
        time = int(datetime.now().timestamp())
        cooldown = doc["passive_cooldown"]
        if time - cooldown < 43200:
            await ctx.reply(f"You are on cooldown! You can change your passive mode <t:{cooldown + 43200}:R>.", mention_author=False)
            return
        collection.update_one({"_id": ctx.author.id}, {"$set": {"passive": choice, "passive_cooldown": time}})
        await ctx.reply(f"You have set your passive mode to {choice}.", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="rob")
    async def rob(self, ctx, user: nextcord.Member):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        user_doc = collection.find_one({"_id": user.id})
        if doc is None or user_doc is None:
            await ctx.reply("You or the user are not opted in to the currency system!", mention_author=False)
            return
        if user.id == ctx.author.id:
            await ctx.reply("You cannot rob yourself!", mention_author=False)
            return
        author_passive = doc["passive"]
        user_passive = user_doc["passive"]
        if author_passive == "True" or user_passive == "True":
            await ctx.reply("You or the user are in passive mode! You cannot rob or be robbed!", mention_author=False)
            return
        time = int(datetime.now().timestamp())
        cooldowns = self.rob_cooldown.get(ctx.author.id, 0)
        if time - cooldowns < 15:
            await ctx.reply(f"You are on cooldown! You can run this command again <t:{cooldowns + 60}:R>.", mention_author=False)
            return
        user_cooldowns = self.user_rob_cooldown.get(user.id, 0)
        if time - user_cooldowns < 600:
            await ctx.reply(f"The user has been robbed recently! They can be robbed again <t:{user_cooldowns + 600}:R>.", mention_author=False)
            return
        rand = random.randint(1, 100)
        self.rob_cooldown[ctx.author.id] = time
        if rand <= 50:
            rand2 = random.randint(1, 20)
            rob_amt = doc["balance"] * (rand2 / 100)
            rob_amt = int(rob_amt)
            new_bal = doc["balance"] - rob_amt
            new_bal = int(new_bal)
            embed = nextcord.Embed(title=f"Rob Failed", description=f"You attemped to rob {user.mention} and failed!\n\nYou were caught by the police and arrested and lost {rand2}% of your balance which was given to {user.mention}!", color=nextcord.Color.red())
            embed.set_footer(text=f"Your new balance is {c} {new_bal:,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1292657124832448584.png")
            await ctx.reply(embed=embed, mention_author=False)
            collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": new_bal}})
            collection.update_one({"_id": user.id}, {"$inc": {"balance": rob_amt}})
            await ctx.message.add_reaction(RED_X)
            await user.send(f"You have been robbed by {ctx.author.mention}! They failed to rob you and you have been given `{c} {rob_amt:,}`!")
            return
        else:
            rand2 = random.randint(1, 100)
            rob_amt = user_doc["balance"] * (rand2 / 100)
            rob_amt = int(rob_amt)
            new_bal = doc["balance"] + rob_amt
            embed = nextcord.Embed(title=f"Rob Successful", description=f"You attemped to rob {user.mention} and successfully robbed them!\n\nYou stole {rand2}% of their balance, which equates to `{c} {rob_amt:,}`", color=nextcord.Color.green())
            embed.set_footer(text=f"Your new balance is {c} {new_bal:,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/894458233769558096.gif")
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)
            self.user_rob_cooldown[user.id] = time
            await user.send(f"You have been robbed by {ctx.author.mention}! They stole {rand2}% of your balance, which equates to `{c} {rob_amt:,}`!")
            collection.update_one({"_id": user.id}, {"$inc": {"balance": -rob_amt}})
            collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": new_bal}})
            await self.update_xp(ctx)
        

    @commands.command(name="give")
    async def give(self, ctx, user: nextcord.Member, quantity: str):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        balance = doc["balance"]

        quan = await self.get_quantity(quantity)
        if quan is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        if quan < 0 or quan > balance:
            await ctx.reply("You do not have enough balance to give that amount.", mention_author=False)
            return
        collection.update_one({"_id": ctx.author.id}, {"$inc": {"balance": -quan}})
        collection.update_one({"_id": user.id}, {"$inc": {"balance": quan}})
        await ctx.reply(f"You have given {user.mention} {c} {quan:,}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        await user.send(f"You have been given `{c} {quan:,}` by {ctx.author.mention}!")

    @commands.command(name="adminset", aliases=["as"])
    async def adminset(self, ctx, user: nextcord.Member, quantity: str):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply("You do not have permission to use this command.", mention_author=False)
            return
        quan = await self.get_quantity(quantity)
        if quan is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        collection.update_one({"_id": user.id}, {"$set": {"balance": quan}})
        await ctx.reply(f"Set {user.name}'s balance to {c} {quan:,}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="admindelete", aliases=["ad"])
    async def admindelete(self, ctx, user: nextcord.Member):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        if not ctx.author.guild_permissions.administrator:
            await ctx.reply("You do not have permission to use this command.", mention_author=False)
            return
        collection.delete_one({"_id": user.id})
        await ctx.reply(f"Deleted {user.name}'s data.", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="snakeeyes", aliases=["se"])
    async def snakeeyes(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        img = "https://cdn.pixabay.com/animation/2023/03/21/10/41/10-41-09-561_512.gif"
        doc = collection.find_one({"_id": ctx.author.id})
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        time = int(datetime.now().timestamp())
        cooldowns = self.se_cooldown.get(ctx.author.id, 0)
        if time - cooldowns < 15:
            await ctx.reply(f"You are on cooldown! You can run this command again <t:{cooldowns + 15}:R>.", mention_author=False)
            return
        self.se_cooldown[ctx.author.id] = time
        balance = doc["balance"]
        split = ctx.message.content.split(" ")
        if len(split) <= 1:
            await ctx.reply("Please enter a valid quantity.", mention_author=False)
            return
        quantity = await self.get_quantity(split[1])
        if quantity is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        if quantity > balance:
            await ctx.reply("You do not have enough balance to play this game.", mention_author=False)
            return
        if quantity > 100000000 or quantity < 1:
            await ctx.reply("You cannot bet more than 100,000,000.", mention_author=False)
            return
        first = random.choice([dice_1, dice_2, dice_3, dice_4, dice_5, dice_6])
        second = random.choice([dice_1, dice_2, dice_3, dice_4, dice_5, dice_6])
        balance = balance - quantity
        if first == second:
            bet_win = "3X"
            if first == dice_1:
                win_amount = quantity * 7
                bet_win = "7X"
            elif first == dice_6:
                win_amount = quantity * 5
                bet_win = "5X"
            elif first == dice_3:
                win_amount = quantity * 4
                bet_win = "4X"
            elif first == dice_2:
                win_amount = quantity * 4
                bet_win = "4X"
            else:
                win_amount = quantity * 3
            balance += int(win_amount)
            collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": balance}})
            embed = nextcord.Embed(title=f"{ctx.author.name}'s snake eyes", description=f"You rolled two dice and bet `{c} {quantity:,}` on it.\n# {first} {second}\n\nYou won your bet by {bet_win}! Your new balance is `{c} {balance:,}`", color=nextcord.Color.green())
            embed.set_footer(text=f"You won {c} {int(win_amount):,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=img)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": balance}})
            embed = nextcord.Embed(title=f"{ctx.author.name}'s snake eyes", description=f"You rolled two dice and bet `{c} {quantity:,}` on it.\n# {first} {second}\n\nYou lost your bet! Your new balance is `{c} {balance:,}`", color=nextcord.Color.red())
            embed.set_footer(text=f"You lost {c} {quantity:,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=img)
            await ctx.reply(embed=embed, mention_author=False)
        await self.update_xp(ctx)

    @commands.command(name="roulette", aliases=["rt"])
    async def roulette(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        img = "https://img1.picmix.com/output/stamp/normal/4/5/9/5/1515954_ea5fd.gif"
        doc = collection.find_one({"_id": ctx.author.id})
        black = ["black", "b"]
        red = ["red", "r"]
        green = ["green", "g"]
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        time = int(datetime.now().timestamp())
        cooldowns = self.rt_cooldown.get(ctx.author.id, 0)
        if time - cooldowns < 15:
            await ctx.reply(f"You are on cooldown! You can run this command again <t:{cooldowns + 15}:R>.", mention_author=False)
            return
        self.rt_cooldown[ctx.author.id] = time
        split = ctx.message.content.split(" ")
        if len(split) != 3:
            await ctx.reply("Please enter a valid quantity and choice of color - black, red, or green.", mention_author=False)
            return
        quantity = await self.get_quantity(split[1])
        choice = split[2]
        balance = doc["balance"]
        if quantity is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        if quantity > balance:
            await ctx.reply("You do not have enough balance to bet that amount.", mention_author=False)
            return
        if quantity > 100000000 or quantity < 1:
            await ctx.reply("You cannot bet more than 100,000,000.", mention_author=False)
            return
        if choice not in black + red + green:
            await ctx.reply("Please enter a valid choice.", mention_author=False)
            return
        
        if choice in black:
            choice = "black"
        elif choice in red:
            choice = "red"
        elif choice in green:
            choice = "green"

        rand = random.randint(1, 36)
        bot_choice = "black"
        balance = balance - quantity
        emoji = "⬛"
        if rand == 36:
            bot_choice = "green"
            emoji = "🟩"
        elif rand < 18:
            bot_choice = "red"
            emoji = "🟥"
        else:
            bot_choice = "black"
            emoji = "⬛"
        bet_win = "2X"
        if choice == bot_choice and choice == "green":
            win_amount = quantity * 10
            bet_win = "10X"
        elif choice == bot_choice:
            win_amount = quantity * 2
        else:
            win_amount = 0
        new_bal = balance + int(win_amount)
        collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": new_bal}})
        win_amount = new_bal - doc["balance"]
        win_amount = abs(win_amount)
        if choice == bot_choice:
            embed = nextcord.Embed(title=f"{ctx.author.name}'s roulette", description=f"You spun the wheel and it landed on **{bot_choice}**.\n# {emoji}\n\nYou chose **{choice}** which was correct! You won your bet by {bet_win}! Your new balance is `{c} {new_bal:,}`", color=nextcord.Color.green())
            embed.set_footer(text=f"You won {c} {int(win_amount):,}", icon_url=ctx.guild.icon.url)
        else:
            embed = nextcord.Embed(title=f"{ctx.author.name}'s roulette", description=f"You spun the wheel and it landed on **{bot_choice}**.\n# {emoji}\n\nYou chose **{choice}** which was incorrect! You lost your bet! Your new balance is `{c} {new_bal:,}`", color=nextcord.Color.red())
            embed.set_footer(text=f"You lost {c} {int(win_amount):,}", icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=img)    
        await ctx.reply(embed=embed, mention_author=False)
        await self.update_xp(ctx)
        
    @commands.command(name="coinflip", aliases=["cf"])
    async def coinflip(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        head_choices = ["heads", "h", "head"]
        tail_choices = ["tails", "t", "tail"]
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        balance = doc["balance"]
        split = ctx.message.content.split(" ")
        if len(split) <= 1:
            await ctx.reply("Please enter a valid quantity and choice - heads or tails.", mention_author=False)
            return
        if len(split) <= 2:
            random_choice = random.choice(["heads", "tails"])
            split.append(random_choice)
        time = int(datetime.now().timestamp())
        cooldowns = self.cf_cooldown.get(ctx.author.id, 0)
        if time - cooldowns < 15:
            await ctx.reply(f"You are on cooldown! You can run this command again <t:{cooldowns + 15}:R>.", mention_author=False)
            return
        self.cf_cooldown[ctx.author.id] = time
        quantity = await self.get_quantity(split[1])
        user_choice = split[2]
        if quantity is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        if quantity > balance:
            await ctx.reply("You do not have enough balance to bet that amount.", mention_author=False)
            return
        if quantity > 100000000 or quantity < 1:
            await ctx.reply("You cannot bet more than 100,000,000.", mention_author=False)
            return
        choice = random.choice([HEADS, TAILS])
        if user_choice in head_choices:
            user_choice = HEADS
            user_choice_text = "heads"
        elif user_choice in tail_choices:
            user_choice = TAILS
            user_choice_text = "tails"
        else:
            await ctx.reply("Please enter a valid choice.", mention_author=False)
            return
        
        if choice == HEADS:
            bot_choice = "heads"
        else:
            bot_choice = "tails"
        
        if choice == user_choice:
            balance += quantity
            collection.update_one({"_id": ctx.author.id}, {"$inc": {"balance": quantity}})
            embed = nextcord.Embed(title=f"{ctx.author.name}'s coinflip", description=f"You risked `{c} {quantity:,}` on a coinflip and the bot chose {bot_choice} and you chose {user_choice_text}.\n\nYou won your bet! Your new balance is `{c} {balance:,}`", color=nextcord.Color.green())
            embed.set_footer(text=f"You won {c} {quantity:,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=choice)
            await ctx.reply(embed=embed, mention_author=False)
        else:
            balance -= quantity
            collection.update_one({"_id": ctx.author.id}, {"$inc": {"balance": -quantity}})
            embed = nextcord.Embed(title=f"{ctx.author.name}'s coinflip", description=f"You risked `{c} {quantity:,}` on a coinflip and the bot chose {bot_choice} and you chose {user_choice_text}.\n\nYou lost your bet! Your new balance is `{c} {balance:,}`", color=nextcord.Color.red())
            embed.set_footer(text=f"You lost {c} {quantity:,}", icon_url=ctx.guild.icon.url)
            embed.set_thumbnail(url=choice)
            await ctx.reply(embed=embed, mention_author=False)
        await self.update_xp(ctx)

    @commands.command(name="gambleroll", aliases=["gr", "groll"])
    async def gambleroll(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        doc = collection.find_one({"_id": ctx.author.id})
        if doc is None:
            await ctx.reply("You are not opted in to the currency system!", mention_author=False)
            return
        time = int(datetime.now().timestamp())
        cooldowns = self.gr_cooldown.get(ctx.author.id, 0)
        if time - cooldowns < 22:
            await ctx.reply(f"You are on cooldown! You can run this command again <t:{cooldowns + 22}:R>.", mention_author=False)
            return
        self.gr_cooldown[ctx.author.id] = time
        split = ctx.message.content.split(" ")
        quantity = await self.get_quantity(split[1])
        if quantity is None:
            await ctx.reply("Unable to process quantity. Please enter a valid quantity.", mention_author=False)
            return
        number = random.choice([1, 2, 3, 4, 5, 6])
        balance = doc["balance"]
        dict = {1: -1, 2: -0.5, 3: 0, 4: 0.25, 5: 0.5, 6: 1}
        if quantity > balance:
            await ctx.reply("You do not have enough balance to bet that amount.", mention_author=False)
            return
        if quantity > 150000000 or quantity < 1:
            await ctx.reply("You cannot bet more than 150,000,000.", mention_author=False)
            return
        balance += int(quantity * dict[number])
        collection.update_one({"_id": ctx.author.id}, {"$set": {"balance": balance}})
        msg = {1: f"You rolled **1** and lost all of your bet.", 2: f"You rolled **2** and lost half of your bet.", 3: f"You rolled **3** and got nothing.", 4: f"You rolled **4** and won 25% of your bet.", 5: f"You rolled **5** and won 50% of your bet.", 6: f"You rolled **6** and won your bet."}
        msg = msg[number]
        footer_icon = ctx.guild.icon.url if ctx.guild.icon else None
        embed = nextcord.Embed(
            title=f"{ctx.author.name}'s gamble roll", description=f"You rolled dice and bet `{c} {quantity:,}` on it. \n\n{msg}\n\nYour new balance is `{c} {balance:,}`", color=nextcord.Color.blurple())
        if dict[number] > 0:
            embed.set_footer(text=f"You won {c} {int(quantity * dict[number]):,}", icon_url=footer_icon)
        elif dict[number] == 0:
            embed.set_footer(text=f"You got nothing.", icon_url=footer_icon)
        else:
            embed.set_footer(text=f"You lost {c} {int(quantity * dict[number]):,}", icon_url=footer_icon)
        embed.set_thumbnail(url="https://i.imgur.com/CTZGCrv.gif")
        await ctx.reply(embed=embed, mention_author=False)
        await self.update_xp(ctx)

    @commands.command(name="balance", aliases=["bal"])
    async def balance(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        con = ctx.message.content.split(" ")
        user = ctx.author.id
        if len(con) != 1:
            user = con[1]
            user = user.replace("<", "").replace(">", "").replace("@", "")
            user = int(user)
        data = collection.find_one({"_id": user})
        if not data:
            await ctx.reply("Please opt-in by running `-optin`.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        coin = "<a:coins:1277758958945435668>"
        user = await self.bot.fetch_user(user)
        descp = f"{coin} **Balance:** {c} {data['balance']:,}\n🏦 **Bank:** {c} {data['bank']:,}\n🧪 **Level:** {data['level']}\n💎 **XP:** {data['xp']:,}\n💰 **Passive:** {data['passive']}"
        embed = nextcord.Embed(title=f"{user.name}'s Balance", description=descp, color=nextcord.Color.blurple())
        all_users = list(collection.find().sort("balance", -1))
        rank = next((i + 1 for i, doc in enumerate(all_users) if doc["_id"] == user.id), 0)
        embed.set_footer(text=f"Guild Rank: #{rank}", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        await ctx.reply(embed=embed, mention_author=False)
        await self.update_xp(ctx)

    @commands.command(name="leaderboard", aliases=["lb"])
    async def leaderboard(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if await self.check_channel(ctx):
            return
        if await self.check_ban(ctx):
            return
        left_arrow = "<a:arrow_left:1316079524710191156>"
        right_arrow = "<a:arrow_right:1316079547124285610>"
        all_users = list(collection.find().sort("balance", -1))
        
        pages = []
        for i in range(0, len(all_users), 10):
            page = nextcord.Embed(title="Leaderboard", color=nextcord.Color.blurple())
            description = ""
            for j, user in enumerate(all_users[i:i+10], start=i+1):
                description += f"{j}. <@{user['_id']}> - {c} {user['balance']:,}\n"
            page.description = description
            page.set_footer(text=f"Page {len(pages) + 1}/{(len(all_users) + 9) // 10}")
            pages.append(page)
            
        if not pages:
            await ctx.reply("No users found!", mention_author=False)
            return
            
        current_page = 0
        
        left_button = nextcord.ui.Button(emoji=left_arrow, disabled=True)
        right_button = nextcord.ui.Button(emoji=right_arrow, disabled=len(pages) == 1)
        
        async def left_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                return
            current_page -= 1
            left_button.disabled = current_page == 0
            right_button.disabled = False
            await interaction.message.edit(embed=pages[current_page], view=view)
            await interaction.response.defer()
            
        async def right_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                return
            current_page += 1
            left_button.disabled = False
            right_button.disabled = current_page == len(pages) - 1
            await interaction.message.edit(embed=pages[current_page], view=view)
            await interaction.response.defer()
            
        left_button.callback = left_callback
        right_button.callback = right_callback
        
        view = nextcord.ui.View()
        view.add_item(left_button)
        view.add_item(right_button)
        
        await ctx.reply(embed=pages[0], view=view, mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if message.author.id not in self.cache:
                return
            if message.guild.id != RC_ID:
                return
            user_time = self.cooldown.get(message.author.id, 0)
            time = int(datetime.now().timestamp())
            if time - user_time < 8:
                return
            self.cooldown[message.author.id] = time
            asyncio.create_task(self.update_coins(message))
        except:
            return

def setup(bot):
    bot.add_cog(Currency(bot))
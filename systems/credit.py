import nextcord
import asyncio
from nextcord.ext import commands
import json
from utils.mongo_connection import MongoConnection

with open("config.json", "r") as file:
    config = json.load(file)

DICT = {"wolfia": "Wolfia", "wolf": "Wolfia", "Rumble Royale": "Rumble Royale", "rumble": "Rumble Royale", "Hangry Game": "Hangry Game", "hangry": "Hangry Game", "gti": "Guess the Item", "sos": "Split or Steal", "Bingo": "Bingo", "Blackjack": "Blackjack", "Rollout": "Rollout", "Hot Potato": "Hot Potato", "rlgl": "Red Light Green Light", "Russian Roulette": "Russian Roulette", "Skribbl": "Skribbl", "Wordle": "Wordle", "Mudae Tea Game": "Mudae Tea Game", "blacktea": "Mudae Tea Game", "yellowtea": "Mudae Tea Game", "redtea": "Mudae Tea Game", "mixtea": "Mudae Tea Game", "greentea": "Mudae Tea Game", "Gartic": "Gartic", "gtn": "Guess the Number", "Guess the Number": "Guess the Number", "Bloony Battle": "Bloony Battle", "UNO": "UNO", "Rollkill": "Rollkill", "black tea": "Mudae Tea Game", "yellow tea": "Mudae Tea Game", "red tea": "Mudae Tea Game", "mix tea": "Mudae Tea Game", "green tea": "Mudae Tea Game", "rumb": "Rumble Royale"}
POINTS = {"Wolfia": 3, "Rumble Royale": 2, "Hangry Game": 2, "Guess the Item": 2, "Split or Steal": 2, "Bingo": 3, "Blackjack": 1, "Rollout:": 2, "Hot Potato": 2, "Red Light Green Light": 2, "Russian Roulette": 1, "Skribbl": 5, "Mudae Tea Game": 3, "Gartic": 3, "Guess the Number": 2, "Bloony Battle": 2, "Wordle": 1, "Mafia Game": 5, "Auction": 2, "Giveaway": 1, "UNO": 6, "Rollkill": 2, "Heist": 3, "Other": 1, "Ghosty": 1}
LOG = 1254624889621708900
RC_ID = 1205270486230110330
MPING = "<@&1205270486263795712>"
MINIPING = "<@&1286097140942377032>"
APING = "<@&1241563195731349504>" 
HPING = "<@&1205270486263795719>"
EPING = "<@&1205270486263795720>"
RPING = "<@&1273737523042189372>"
GHOSTYPING = "<@&1392182028706910298>"
GPING = ["<@&1205270486276251689>", "<@&1218714110502506586>", "<@&1205270486276251688>", "<@&1205270486246883349>", "<@&1207242044502835231>"]
GRAY = 8421504
PINGSLICE = ["<@&1205270486263795712>", "<@&1286097140942377032>", "<@&1241563195731349504>", "<@&1205270486263795720>", "<@&1205270486276251689>", "<@&1218714110502506586>", "<@&1205270486276251688>", "<@&1205270486246883349>", "<@&1207242044502835231>"]
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Credit"]

class Credit(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Credit cog loaded.")

    @commands.command(name="credit")
    async def credit_cmd(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if not ctx.message.author.guild_permissions.manage_messages:
            return
        if ctx.message.content.startswith("-credit add") or ctx.message.content.startswith(".credit add") or ctx.message.content.startswith("!credit add"):
            if ctx.author.guild_permissions.administrator:
                await self.add_credit(ctx)
            else:
                await ctx.message.add_reaction(RED_X)
        elif ctx.message.content.startswith("-credit remove") or ctx.message.content.startswith(".credit remove") or ctx.message.content.startswith("!credit remove"):
            if ctx.author.guild_permissions.administrator:
                await self.remove_credit(ctx)
            else:
                await ctx.message.add_reaction(RED_X)
        elif ctx.message.content.startswith("-credit reset") or ctx.message.content.startswith(".credit reset") or ctx.message.content.startswith("!credit reset"):
            if ctx.author.guild_permissions.administrator:
                await self.reset_credit(ctx)
            else:
                await ctx.message.add_reaction(RED_X)
        elif ctx.message.content.startswith("-credit lb") or ctx.message.content.startswith(".credit lb") or ctx.message.content.startswith("!credit lb"):
            await self.credit_leaderboard(ctx)
        elif ctx.message.content.startswith("-credit total") or ctx.message.content.startswith(".credit total") or ctx.message.content.startswith("!credit total"):
            await self.total_credit(ctx)
        else:
            usr = ctx.message.author
            arg = ctx.message.content.split(" ")
            if len(arg) == 1:
                pass
            elif len(arg) == 2 and arg[1].lower() != "all":
                con = arg[1].replace("<@", "").replace(">", "")
                usr = self.bot.get_user(int(con))
            elif arg[1].lower() == "all":
                role1 = ctx.guild.get_role(1205270486469058634).members
                role2 = ctx.guild.get_role(1206299567520354317).members
                all_mems = role1 + role2
                staff_list = []
                for mem in all_mems:
                    if mem.id != 939307545019969536:
                        staff_list.append(mem)
                for staff in staff_list:
                    await self.credit_score(ctx, staff)
                return
            await self.credit_score(ctx, usr)

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            if "<@&" not in message.content:
                return
            elif message.author.bot or not message.author.guild_permissions.manage_messages or message.guild.id != RC_ID:
                return
        except:
            return
        user_roles = [role.id for role in message.author.roles]
        allowed = [1206299567520354317, 1205270486469058637]
        if not any(role in user_roles for role in allowed):
            return
        
        asyncio.create_task(self.detect_ping(message))
        return

    async def total_credit(self, ctx):
        doc = collection.find_one({"_id": "total_credit"})["Points"]
        sorted_leaderboard = sorted(doc.items(), key=lambda item: item[1], reverse=True)
        
        pages = []
        current_position = 1
        last_points = None
        
        for i in range(0, len(sorted_leaderboard), 10):
            page_message = ""
            page_entries = sorted_leaderboard[i:i+10]
            
            for index, (user_id, points) in enumerate(page_entries, start=i):
                if points != last_points:
                    current_position = index + 1
                page_message += f"{current_position}. <@{user_id}> | {points} Points\n"
                last_points = points
                
            embed = nextcord.Embed(title="Credit Total Leaderboard", description=page_message, color=16776960)
            embed.set_footer(text=f"Logged since 12/8/2024 • Page {len(pages)+1}/{(len(sorted_leaderboard)-1)//10+1}", 
                           icon_url=ctx.message.author.avatar.url)
            pages.append(embed)

        if not pages:
            embed = nextcord.Embed(title="Credit Total Leaderboard", description="No entries found.", color=16776960)
            embed.set_footer(text="Logged since 12/8/2024", icon_url=ctx.message.author.avatar.url)
            await ctx.reply(embed=embed, mention_author=False)
            return

        current_page = 0
        
        view = nextcord.ui.View()
        
        async def previous_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                return
            current_page = (current_page - 1) % len(pages)
            prev_button.disabled = current_page == 0
            next_button.disabled = current_page == len(pages) - 1
            await interaction.message.edit(embed=pages[current_page], view=view)

        async def next_callback(interaction):
            nonlocal current_page
            if interaction.user != ctx.author:
                return
            current_page = (current_page + 1) % len(pages)
            prev_button.disabled = current_page == 0
            next_button.disabled = current_page == len(pages) - 1
            await interaction.message.edit(embed=pages[current_page], view=view)

        prev_button = nextcord.ui.Button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.gray)
        next_button = nextcord.ui.Button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.gray)
        
        prev_button.callback = previous_callback
        next_button.callback = next_callback
        prev_button.disabled = True
        next_button.disabled = len(pages) <= 1

        view.add_item(prev_button)
        view.add_item(next_button)

        await ctx.reply(embed=pages[0], view=view, mention_author=False)

    async def reset_credit(self, ctx):
        collection.delete_one({"_id": "credit_score"})
        collection.insert_one({"_id": "credit_score", "Points": {}})
        await ctx.message.add_reaction(GREEN_CHECK)
        embed = nextcord.Embed(title="Database Reset", description="Credit database has been reset. All credit scores have been set to 0.", color=65280)
        embed.set_footer(text=f"Requested by {ctx.message.author.name}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)

    async def remove_credit(self, ctx):
        args = ctx.message.content.split(" ")
        user = args[2]
        points = int(args[3])
        if len(args) < 4:
            await ctx.send("Invalid command usage. Use -credit remove <user> <points>")
            return
        
        user_id = int(user.strip("<@!>"))
        doc = collection.find_one({"_id": "credit_score"})
        points = -points
        if not doc:
            collection.insert_one({"_id": "credit_score", "Points": {user_id: points}, f"{user_id}": {"Bonus": points}})
            await ctx.message.add_reaction(GREEN_CHECK)
        else:
            collection.update_one(
                {"_id": "credit_score"},
            {"$inc": {f"Points.{user_id}": points, f"{str(user_id)}.Bonus": points}}
        )
        collection.update_one(
            {"_id": "total_credit"},
            {"$inc": {f"Points.{user_id}": points, f"{str(user_id)}.Bonus": points}}
        )
        user = ctx.guild.get_member(user_id)
        await ctx.message.add_reaction(GREEN_CHECK)
        embed = nextcord.Embed(title="Credit Assigned", description=f"**Target:** {user.mention}\n**Removed:** {points} Points\n**Type:** Administrative Action\n**From:** {ctx.message.author.mention}", color=65280)
        embed.set_footer(text="All systems operational.")
        embed.set_thumbnail(url="https://i.imgur.com/iYBkQq3.png")
        await self.bot.get_channel(LOG).send(embed=embed)

    async def credit_leaderboard(self, ctx):
        doc = collection.find_one({"_id": "credit_score"})["Points"]
        sorted_leaderboard = sorted(doc.items(), key=lambda item: item[1], reverse=True)
        leaderboard_message = ""
        current_position = 1
        last_points = None
        for index, (user_id, points) in enumerate(sorted_leaderboard):
            if points != last_points:
                current_position = index + 1
            leaderboard_message += f"{current_position}. <@{user_id}> | {points} Points\n"
            last_points = points

        embed = nextcord.Embed(title="Credit Leaderboard", description=leaderboard_message, color=GRAY)
        embed.set_footer(text=f"Requested by {ctx.message.author.name}", icon_url=ctx.message.author.avatar.url)
        embed.color = 16776960
        await ctx.reply(embed=embed, mention_author=False)
        

    async def add_credit(self, ctx):
        args = ctx.message.content.split(" ")
        user = args[2]
        points = int(args[3])
        if len(args) < 4:
            await ctx.send("Invalid command usage. Use -credit add <user> <points>")
            return
        
        user_id = int(user.strip("<@!>"))
        doc = collection.find_one({"_id": "credit_score"})
        if not doc:
            collection.insert_one({"_id": "credit_score", "Points": {user_id: points}, f"{user_id}": {"Bonus": points}})
            await ctx.message.add_reaction(GREEN_CHECK)
        else:
            collection.update_one(
                {"_id": "credit_score"},
            {"$inc": {f"Points.{user_id}": points, f"{str(user_id)}.Bonus": points}}
        )
        collection.update_one(
            {"_id": "total_credit"},
            {"$inc": {f"Points.{user_id}": points, f"{str(user_id)}.Bonus": points}}
        )
        user = ctx.guild.get_member(user_id)
        await ctx.message.add_reaction(GREEN_CHECK)
        points = abs(points)
        embed = nextcord.Embed(title="Credit Assigned", description=f"**Target:** {user.mention}\n**Added:** {points} Points\n**Type:** Administrative Action\n**From:** {ctx.message.author.mention}", color=65280)
        embed.set_footer(text="All systems operational.")
        embed.set_thumbnail(url="https://i.imgur.com/iYBkQq3.png")
        await self.bot.get_channel(LOG).send(embed=embed)

    async def detect_ping(self, message):

        if MPING in message.content:
            type = "Mafia Game"
        elif APING in message.content:
            type = "Auction"
        elif HPING in message.content:
            type = "Heist"
        elif any(ping in message.content for ping in GPING):
            type = "Giveaway"
        elif EPING in message.content and RPING in message.content:
            type = "Rumble Royale"
        elif GHOSTYPING in message.content:
            type = "Ghosty"
        else:
            type = "event"
            ping = message.content.split("<@&")[1].split(">")[0]
            ping = f"<@&{ping}>"
            if not ping == EPING and not ping == MINIPING:
                return

        if type == "Mafia Game" or type == "Auction" or type == "Giveaway" or type == "Heist":
            points_to_add = POINTS[type]
            if points_to_add:
                collection.update_one(
                    {"_id": "credit_score"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.{type}": 1}}
                )
                collection.update_one(
                    {"_id": "total_credit"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.{type}": 1}}
                )
                embed = nextcord.Embed(title="Credit Increment", description=f"**Target:** {message.author.mention}\n**Reward:** {points_to_add} Points\n**Reason:** Event Host\n**Type:** [{type}]({message.jump_url})", color=65280)
                embed.set_footer(text="All systems operational.")
                embed.set_thumbnail(url="https://i.imgur.com/tTpRLgK.png")
                await self.bot.get_channel(LOG).send(embed=embed)
        if type == "Rumble Royale":
            points_to_add = POINTS["Rumble Royale"]
            if points_to_add:
                collection.update_one(
                    {"_id": "credit_score"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.Rumble Royale": 1}}
                )
                collection.update_one(
                    {"_id": "total_credit"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.Rumble Royale": 1}}
                )
                embed = nextcord.Embed(title="Credit Increment", description=f"**Target:** {message.author.mention}\n**Reward:** {points_to_add} Points\n**Reason:** Event Host\n**Type:** [{type}]({message.jump_url})", color=65280)
                embed.set_footer(text="All systems operational.")
                embed.set_thumbnail(url="https://i.imgur.com/tTpRLgK.png")
                await self.bot.get_channel(LOG).send(embed=embed)
        elif type == "Ghosty":
            points_to_add = POINTS["Ghosty"]
            if points_to_add:
                collection.update_one(
                    {"_id": "credit_score"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.Ghosty": 1}}
                )
                collection.update_one(
                    {"_id": "total_credit"},
                    {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.Ghosty": 1}}
                )
                embed = nextcord.Embed(title="Credit Increment", description=f"**Target:** {message.author.mention}\n**Reward:** {points_to_add} Points\n**Reason:** Event Host\n**Type:** [{type}]({message.jump_url})", color=65280)
                embed.set_footer(text="All systems operational.")
                embed.set_thumbnail(url="https://i.imgur.com/tTpRLgK.png")
                await self.bot.get_channel(LOG).send(embed=embed)
        elif type == "event":
            matched_event = None
            try:
                for key in DICT.keys():
                    if key.lower() in message.content.lower():
                        matched_event = DICT[key]
                        break
            except Exception as e:
                print(f"Error in detect_ping: {e}")
                return
            if matched_event is None:
                matched_event = "Other"
            if matched_event:
                try:
                    points_to_add = POINTS.get(matched_event, 0)
                except Exception as e:
                    print(f"Error in detect_ping: {e}")
                    return
                if points_to_add:
                    try:
                        collection.update_one(
                            {"_id": "credit_score"},
                            {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.{matched_event}": 1}}
                        )
                        collection.update_one(
                            {"_id": "total_credit"},
                            {"$inc": {f"Points.{message.author.id}": points_to_add, f"{str(message.author.id)}.{matched_event}": 1}}
                        )
                    except Exception as e:
                        print(f"Error in detect_ping: {e}")
                        return
                    embed = nextcord.Embed(title="Credit Increment", description=f"**Target:** {message.author.mention}\n**Reward:** {points_to_add} Points\n**Reason:** Event Host\n**Type:** [{matched_event}]({message.jump_url})", color=65280)
                    embed.set_footer(text="All systems operational.")
                    embed.set_thumbnail(url="https://i.imgur.com/tTpRLgK.png")
                    await self.bot.get_channel(LOG).send(embed=embed)

            
            

    async def credit_score(self, ctx, user):
        try:
            usr = user.id
            str_usr = str(usr)
            doc = collection.find_one({"_id": "credit_score"})
            if doc:
                points = doc.get("Points", {}).get(str_usr, "None")
                data = doc.get(str_usr, {})
                position = "None"
                if data:
                    events = ""
                    points_dict = doc.get("Points", {})
                    sorted_points = sorted(points_dict.items(), key=lambda item: item[1], reverse=True)
                    position = next((index + 1 for index, (user_id, _) in enumerate(sorted_points) if user_id == str_usr), "None")
                    for key, value in data.items():
                        if value != 0:
                            if events != "":
                                events = f"{events} / {value} {key}"
                            else:
                                events = f"{value} {key}"
                else:
                    events = "None"
            else:
                points = "None"
                events = "None"
                position = "None"
        except Exception as e:
            print(f"Error in credit_score: {e}")
            points = "Error"
            events = "Error"
            position = "Error"

        if events == "":
            events = "None"
        descp = f"**Target:** {user.mention}\n**Position:** {position}\n**Points:** {points}\n**Events:** {events}"
        embed = nextcord.Embed(title="Credit Report", description=descp, color=GRAY)
        avatar = user.display_avatar.url
        embed.set_thumbnail(url=avatar)
        embed.set_footer(text=f"Requested by {ctx.message.author.name}", icon_url=ctx.message.author.avatar.url)
        await ctx.send(embed=embed)
        

def setup(bot):
    bot.add_cog(Credit(bot))

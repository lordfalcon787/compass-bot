import nextcord
from datetime import datetime
from nextcord.ext import commands, application_checks
import json
import os
import random

with open("config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]
BOT_OWNER = config["bot_owner"]
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()

acollection = db["Admin"]
collection = db["Misc"]
fun_collection = db["Fun Commands"]

extensions = collection.find_one({"_id": "extensions"})["extensions"]

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Admin cog is ready.")

    @nextcord.slash_command(name="ping", description="Check bot latency.")
    async def ping_slash(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(content=f"PONG! Bot Latency: `{self.bot.latency * 1000:.2f}ms`", ephemeral=True)

    @nextcord.slash_command(name="aping", description="Check bot latency + Discord API Latency + MongoDB Latency")
    async def aping_slash(self, interaction: nextcord.Interaction):
        before = datetime.now()
        message = await interaction.response.send_message(content=f"PONG! Bot Latency: `{self.bot.latency * 1000:.2f}ms`", ephemeral=True)
        after = datetime.now()
        discord_latency = (after - before).total_seconds() * 1000
        await message.edit(content=f"PONG! Bot Latency: `{self.bot.latency * 1000:.2f}ms`\nAPI Latency: `{discord_latency:.2f}ms`")
        random_number = random.randint(1, 1000000)
        before = datetime.now()
        collection.update_one({"_id": "ping_test"}, {"$set": {"ping": random_number}}, upsert=True)
        after = datetime.now()
        mongo_latency = (after - before).total_seconds() * 1000
        await message.edit(content=f"PONG! Bot Latency: `{self.bot.latency * 1000:.2f}ms`\nAPI Latency: `{discord_latency:.2f}ms`\nMongoDB Latency: `{mongo_latency:.2f}ms`")
        collection.delete_one({"_id": "ping_test"})

    @nextcord.slash_command(name="getcode", description="Get all the bot files.")
    @application_checks.is_owner()
    async def getcode(self, interaction: nextcord.Interaction):
        @staticmethod
        def combine_files(output_file):
            with open(output_file, 'w') as outfile:
                for root, dirs, files in os.walk("cogs"):
                    for file in files:
                        if file.endswith(".py"):
                            with open(os.path.join(root, file), 'r') as infile:
                                outfile.write(infile.read())
                                outfile.write("\n\n")
                with open("bot.py", 'r') as infile:
                    outfile.write(infile.read())
                    outfile.write("\n\n")

        await interaction.response.defer(ephemeral=True)
        combine_files("combined_bot_code.py")
        await interaction.followup.send(file=nextcord.File("combined_bot_code.py"), ephemeral=True)
        os.remove("combined_bot_code.py")

    @commands.command(name="extensions")
    async def extensions(self, ctx):
        if ctx.author.id != BOT_OWNER:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        array = []
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            for extension in extensions:
                array.append(extension)
            embed = nextcord.Embed(title="Extensions", description=f"{array}", color=nextcord.Color.green())
            await ctx.reply(embed=embed, mention_author=False)
            return
        add = split[1:]
        for extension in add:
            array.append(extension)
        collection.update_one({"_id": "extensions"}, {"$set": {"extensions": array}})
        await ctx.reply(content=f"Successfully set extensions to {add}.", mention_author=False)
        return
        
    @commands.command(name="botadmin")
    async def botadmin(self, ctx, user: nextcord.Member):
        if ctx.author.id != BOT_OWNER:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return

        success_embed = nextcord.Embed(title="You are now a Bot Admin!", description=f"You have been added as a bot admin by {ctx.author.mention}. This gives you access to command like:\n\n- `!botban` - Bans a user from using the bot.\n- `!reload` - Reloads all the extensions.\n- `!unload` - Unloads an extension.\n\nAn abuse of this power will result in a ban from the bot.", color=nextcord.Color.green())
        user = user
        doc = acollection.find_one({"_id": "bot_admins"})
        if doc:
            if user.id in doc["admins"]:
                acollection.update_one({"_id": "bot_admins"}, {"$pull": {"admins": user.id}})
                embed = nextcord.Embed(title="Bot Admin Removed", description=f"{user.mention} has been removed as a bot admin.", color=nextcord.Color.red())
                await ctx.reply(embed=embed, mention_author=False)
                await ctx.message.add_reaction(GREEN_CHECK)
                return
            else:
                acollection.update_one({"_id": "bot_admins"}, {"$push": {"admins": user.id}}, upsert=True)
                embed = nextcord.Embed(title="Bot Admin Added", description=f"{user.mention} has been added as a bot admin.", color=nextcord.Color.green())
                await ctx.reply(embed=embed, mention_author=False)
                await ctx.message.add_reaction(GREEN_CHECK)
                try:
                    userr = await self.bot.fetch_user(user.id)
                    await userr.send(embed=success_embed)
                except:
                    pass
        else:
            acollection.insert_one({"_id": "bot_admins", "admins": [user.id]})
            embed = nextcord.Embed(title="Bot Admin Added", description=f"{user.mention} has been added as a bot admin.", color=nextcord.Color.green())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)
            try:
                userr = await self.bot.fetch_user(user.id)
                await userr.send(embed=success_embed)
            except:
                pass

    @commands.command(name="whitelist")
    async def whitelist(self, ctx: commands.Context):
        admins = acollection.find_one({"_id": "bot_admins"})
        if ctx.author.id not in admins["admins"]:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            await ctx.reply("Please provide a user to whitelist.", mention_author=False)
            return
        
        user = split[1]
        user = user.replace("<", "").replace("@", "").replace(">", "")
        user = await self.bot.fetch_user(int(user))
        doc = fun_collection.find_one({"_id": "kill_cmd_whitelist"})
        if doc:
            if user.id in doc["whitelist"]:
                fun_collection.update_one({"_id": "kill_cmd_whitelist"}, {"$pull": {"whitelist": user.id}})
                await ctx.reply(f"Successfully removed {user.mention} from the whitelist.", mention_author=False)
                return
            else:
                fun_collection.update_one({"_id": "kill_cmd_whitelist"}, {"$push": {"whitelist": user.id}}, upsert=True)
                await ctx.reply(f"Successfully whitelisted {user.mention}.", mention_author=False)
                return
        else:
            fun_collection.insert_one({"_id": "kill_cmd_whitelist", "whitelist": [user.id]})
            await ctx.reply(f"Successfully whitelisted {user.mention}.", mention_author=False)
            return
        
    @commands.command(name="aping")
    async def aping(self, ctx):
        api_latency = self.bot.latency * 1000
        before = datetime.now()
        message = await ctx.send(f"Bot Latency: `{api_latency:.2f}ms`")
        after = datetime.now()
        discord_latency = (after - before).total_seconds() * 1000
        await message.edit(content=f"Bot Latency: `{api_latency:.2f}ms`\nAPI Latency: `{discord_latency:.2f}ms`")
        random_number = random.randint(1, 1000000)
        before = datetime.now()
        collection.update_one({"_id": "ping_test"}, {"$set": {"ping": random_number}}, upsert=True)
        after = datetime.now()
        mongo_latency = (after - before).total_seconds() * 1000
        await message.edit(content=f"Bot Latency: `{api_latency:.2f}ms`\nAPI Latency: `{discord_latency:.2f}ms`\nMongoDB Latency: `{mongo_latency:.2f}ms`")
        collection.delete_one({"_id": "ping_test"})

    @commands.command(name="botban")
    async def botban(self, ctx):
        try:
            admins = acollection.find_one({"_id": "bot_admins"})
            if ctx.author.id not in admins["admins"]:
                embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
                await ctx.reply(embed=embed, mention_author=False)
                await ctx.message.add_reaction(RED_X)
                return
            split = ctx.message.content.split(" ")
            user = split[1]
            user = user.replace("<@", "")
            user = user.replace(">", "")
            user = int(user)

            if user == ctx.author.id or user in admins["admins"]:
                embed = nextcord.Embed(title="Invalid Permissions", description="You cannot ban yourself or other bot admins.", color=nextcord.Color.red())
                await ctx.reply(embed=embed, mention_author=False)
                await ctx.message.add_reaction(RED_X)
                return

            doc = collection.find_one({"_id": "bot_banned"})
            if doc:
                if str(user) in doc:
                    doc.pop(str(user))
                    doc["_id"] = "bot_banned"
                    collection.delete_one({"_id": "bot_banned"})
                    collection.insert_one(doc)
                    user = await self.bot.fetch_user(user)
                    embed = nextcord.Embed(title=f"{GREEN_CHECK} | Unban Successful", description=f"User {user.id} ({user.name}) has been unbanned from using the bot.", color=65280)
                    await ctx.reply(embed=embed, mention_author=False)
                    try:
                        await user.send(embed=embed)
                    except:
                        pass
                    return
            if len(split) == 2:
                reason = "No reason provided."
            else:
                reason = split[2:]
                reason = " ".join(reason)
            collection.update_one({"_id": "bot_banned"}, {"$set": {str(user): reason}}, upsert=True)
            user = await self.bot.fetch_user(user)
            embed = nextcord.Embed(title=f"{GREEN_CHECK} | Ban Successful", description=f"User {user.id} ({user.name}) has been banned from using the bot for reason: {reason}", color=65280)
            try:
                await user.send(embed=embed)
            except:
                pass
            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            await ctx.reply(content=f"An error occurred: {str(e)}", mention_author=False)

    @commands.command(name="reload")
    async def reload(self, ctx):
        if ctx.author.id != BOT_OWNER:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        success_count = 0
        fail_count = 0
        fail_list = []

        for extension in extensions:
            try:
                self.bot.reload_extension(extension)
                success_count += 1
            except Exception as e:
                fail_count += 1
                fail_list.append(f"{extension}: {str(e)}")

        result_message = f"Reloaded {success_count} extension(s) successfully."
        if fail_count > 0:
            result_message += f"\nFailed to reload {fail_count} extension(s)."
            if fail_list:
                result_message += "\nFailed extensions:"
                for fail in fail_list:
                    result_message += f"\n- {fail}"

        await ctx.reply(content=result_message, mention_author=False)

    @commands.command(name="load")
    async def load(self, ctx):
        if ctx.author.id != BOT_OWNER:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        extension = f"cogs.{ctx.message.content.split(' ')[1]}"
        try:
            self.bot.load_extension(extension)
            await ctx.reply(content=f"Loaded {extension}.", mention_author=False)
        except Exception as e:
            await ctx.reply(content=f"An error occurred: {str(e)}", mention_author=False)

    @commands.command(name="unload")
    async def unload(self, ctx):
        if ctx.author.id != BOT_OWNER:
            embed = nextcord.Embed(title="Invalid Permissions", description="You do not have the required permissions to use this command.", color=nextcord.Color.red())
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        extension = f"cogs.{ctx.message.content.split(' ')[1]}"
        try:
            self.bot.unload_extension(extension)
            await ctx.reply(content=f"Unloaded {extension}.", mention_author=False)
        except Exception as e:
            await ctx.reply(content=f"An error occurred: {str(e)}", mention_author=False)

def setup(bot):
    bot.add_cog(Admin(bot))

    
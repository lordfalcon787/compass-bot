import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Misc"]

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
CHANNEL = 1205270487085879429

class StaffApps(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"StaffApps cog loaded")

    @commands.command(name="staffapps")
    async def staffapps(self, ctx: commands.Context):
        if ctx.guild.id != 1205270486230110330:
            return
        if not ctx.author.guild_permissions.administrator:
            return
        split = ctx.message.content.split(" ")
        if len(split) < 3:
            await ctx.reply("Correct syntax is `!staffapps [open/close] [mod/eman]`")
            await ctx.message.add_reaction(RED_X)
            return
        arg = split[1].lower()
        if arg == "open":
            await self.open_app(ctx, split)
        elif arg == "close":
            await self.close_app(ctx, split)
        else:
            await ctx.message.add_reaction(RED_X)

    async def open_app(self, ctx: commands.Context, split):
        doc = collection.find_one({"_id": "staff_apps"})
        arg_1 = "CLOSED"
        arg_2 = "CLOSED"
        if doc:
            arg_1 = doc["trial"]
            arg_2 = doc["event"]
        arg = " ".join(split[2:]).lower()
        if "mod" in arg or "trial" in arg:
            arg_1 = "OPEN"
        if "man" in arg or "event" in arg:
            arg_2 = "OPEN"
        embed_1 = nextcord.Embed(title="Staff Applications", description="> **Trial Moderators**\n- Use the panel below this embed to start the application. \n- You must be Level 10 to apply.\n- You must have 2FA (Two-Factor Authentication) enabled on your account.\n- Make sure to read questions carefully and put your best effort in.\n\n> **Event Managers:**\n- Use the panel below this embed to start the application. \n- You must be Level 10 to apply.\n- Make sure to read questions carefully and put your best effort in.\n\n> **Partnership Managers:**\n- Use the panel below this embed to start the application. \n- No requirements! Always open!\n- Make sure to read questions carefully and put your best effort in.")
        embed_1.set_thumbnail(url="https://cdn-icons-png.flaticon.com/128/3093/3093091.png")
        embed_1.color = nextcord.Color.blurple()
        embed_2 = nextcord.Embed(title="Application Status", description=f"**Trial Moderator:** `{arg_1}`\n**Event Manager:** `{arg_2}`\n**Partnership Manager:** `OPEN`")
        embed_2.color = nextcord.Color.blurple()
        embed_2.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/9274/9274447.png")
        embed_2.set_image(url="https://i.imgur.com/cNIVuoA.jpeg")
        current_msg = None
        channel = ctx.guild.get_channel(CHANNEL)
        if doc:
            message_id = doc["id"]
            try:
                current_msg = await channel.fetch_message(message_id)
            except:
                current_msg = None
            if not current_msg:
                current_msg = await channel.send(embeds=[embed_1, embed_2])
            else:
                await current_msg.edit(embeds=[embed_1, embed_2])
        else:
            current_msg = await channel.send(embeds=[embed_1, embed_2])
        collection.update_one({"_id": "staff_apps"}, {"$set": {"id": current_msg.id, "trial": arg_1, "event": arg_2}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)
    
    async def close_app(self, ctx: commands.Context, split):
        doc = collection.find_one({"_id": "staff_apps"})
        arg_1 = "CLOSED"
        arg_2 = "CLOSED"
        if doc:
            arg_1 = doc["trial"]
            arg_2 = doc["event"]
        arg = " ".join(split[2:]).lower()
        if "mod" in arg or "trial" in arg:
            arg_1 = "CLOSED"
        if "man" in arg or "event" in arg:
            arg_2 = "CLOSED"
        embed_1 = nextcord.Embed(title="Staff Applications", description="> **Trial Moderators**\n- Use the panel below this embed to start the application. \n- You must be Level 10 to apply.\n- You must have 2FA (Two-Factor Authentication) enabled on your account.\n- Make sure to read questions carefully and put your best effort in.\n\n> **Event Managers:**\n- Use the panel below this embed to start the application. \n- You must be Level 10 to apply.\n- Make sure to read questions carefully and put your best effort in.\n\n> **Partnership Managers:**\n- Use the panel below this embed to start the application. \n- No requirements! Always open!\n- Make sure to read questions carefully and put your best effort in.")
        embed_1.set_thumbnail(url="https://cdn-icons-png.flaticon.com/128/3093/3093091.png")
        embed_1.color = nextcord.Color.blurple()
        embed_2 = nextcord.Embed(title="Application Status", description=f"**Trial Moderator:** `{arg_1}`\n**Event Manager:** `{arg_2}`\n**Partnership Manager:** `OPEN`")
        embed_2.color = nextcord.Color.blurple()
        embed_2.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/9274/9274447.png")
        embed_2.set_image(url="https://i.imgur.com/cNIVuoA.jpeg")
        current_msg = None
        channel = ctx.guild.get_channel(CHANNEL)
        if doc:
            message_id = doc["id"]
            try:
                current_msg = await channel.fetch_message(message_id)
            except:
                current_msg = None
            if not current_msg:
                current_msg = await channel.send(embeds=[embed_1, embed_2])
            else:
                await current_msg.edit(embeds=[embed_1, embed_2])
        else:
            current_msg = await channel.send(embeds=[embed_1, embed_2])
        collection.update_one({"_id": "staff_apps"}, {"$set": {"id": current_msg.id, "trial": arg_1, "event": arg_2}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)

def setup(bot: commands.Bot):
    bot.add_cog(StaffApps(bot))

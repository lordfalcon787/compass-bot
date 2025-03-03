import nextcord
import asyncio
from nextcord.ext import tasks
from nextcord.ext import commands
from datetime import datetime
import json

import json
from utils.mongo_connection import MongoConnection

with open("config.json", "r") as file:
    config = json.load(file)

ROOT = "<@&1206299567520354317>"
ADMIN = "<@&1205270486502867030>"
DONATE = 1205270487454974055
EVENT_QUEUE = 1267527896218468412
LOG = 1267725321017360424
AUCTION_QUEUE = 1267530934723281009
AUCTION = 1240782193270460476
EMAN = "<@&1205270486469058637>"
GMAN = "<@&1205270486490292244>"
GREEN_CHECK = "<:green_check:1218286675508199434>"
RED_X = "<:red_x:1218287859963007057>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Donosticky"]

MAIN_EMBED = nextcord.Embed(
    title="Donation Information \n",
    description="Use the buttons below to learn more about the donation system. Make sure to read the donation rules before donating. \n \n More notes can be found [here](https://discord.com/channels/1205270486230110330/1253375007057379412)\nAny items that you would like to auction do not need to follow the 75% rule but must follow a 33% rule.\nDo not donate **any items** that don't follow 75% rule\nYour donation will be **fully removed and not refunded**",
    color=3092790
)
MAIN_EMBED.set_footer(
    text="Robbing Central - Made by _lordfalcon_",
    icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512"
)

class View2(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button1 = nextcord.ui.Button(label="How to Donate", style=nextcord.ButtonStyle.primary, custom_id="how_donate")
        button1.callback = self.how_donate_callback
        self.add_item(button1)

        button2 = nextcord.ui.Button(label="Donation Notes", style=nextcord.ButtonStyle.primary, custom_id="donation_notes") 
        button2.callback = self.notes_callback
        self.add_item(button2)

        button3 = nextcord.ui.Button(label="Minimums", style=nextcord.ButtonStyle.primary, custom_id="minimums")
        button3.callback = self.minimums_callback
        self.add_item(button3)

        button4 = nextcord.ui.Button(label="Rules", style=nextcord.ButtonStyle.primary, custom_id="rules")
        button4.callback = self.rules_callback
        self.add_item(button4)

    async def how_donate_callback(self, interaction: nextcord.Interaction):
        desc = "`-event [event] [prize] [other info]` for events.\n`-giveaway [prize] [other info]` for giveaways.\n`-heist [amount] [other info]` for heists.\n`-nitro [event/giveaway] [type]` for nitro donations.\n`-auction [item and quantity]` for auctions.\n`-event raffle [items]` for raffles\n\n__Do not send items for auction, just ping.__"
        embed = nextcord.Embed(title="How to Donate", description=desc)
        embed.set_footer(text="Robbing Central - Made by _lordfalcon_ and ace_of_spadess.", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass

    async def notes_callback(self, interaction: nextcord.Interaction):
        desc = "Events can have many customizations, to learn more about this, as well spree rules and other notes, please read [these notes](https://discord.com/channels/1205270486230110330/1253375007057379412) before ANY donation."
        embed = nextcord.Embed(title="RC Donation Notes", description=desc)
        embed.set_footer(text="Robbing Central - Made by _lordfalcon_ and ace_of_spadess.", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass

    async def minimums_callback(self, interaction: nextcord.Interaction):
        desc = "Chat Rumbles/Events/Ban Battle: `1B`\nUNO: `50M`\nWolfia: `30M`\nMafia/Bingo/Auctions/Raffles/Draw Battle: `30M`\nSpecial Games: `30M`\nHeists: `25M`\nEOT: `20M`\nSOS: `10M`\nRumble, hangry, other events: `5M`\nWordle: `2M` per round"
        embed = nextcord.Embed(title="RC Donation Minimums", description=desc)
        embed.set_footer(text="Robbing Central - Made by _lordfalcon_ and ace_of_spadess.", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass

    async def rules_callback(self, interaction: nextcord.Interaction):
        desc = "<:rulebook:1260566783148949525> No idle chatting.\n<:rulebook:1260566783148949525> No inflated items donations (average value × 0.75 > market/shop actual offer).\n<:rulebook:1260566783148949525> No shop item auction with actual value < ⏣ 30,000,000.\n\n**Example:**\nDonation – No Bean Seeds\nAuction – No Bean Seeds\n\nIf you donate item(s) that violate these rules, the excess donation amount will be removed from your donation bank, please refrain from making this happen.\n\nTo check if your item is elgible, look up the market offers and make there are not any that are 75 percent or less of the market value. e.g. Bean seeds are worth 198K in average value, but you can buy them in shop for 35K which is 17.6 percent (market price/average value)"
        embed = nextcord.Embed(title="RC Donation Rules", description=desc)
        embed.set_footer(text="Robbing Central - Made by _lordfalcon_ and ace_of_spadess.", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            try:
                await interaction.followup.send(embed=embed, ephemeral=True)
            except:
                pass

class View(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.lock = asyncio.Lock()

        accept = nextcord.ui.Button(label="Accept", style=nextcord.ButtonStyle.green, custom_id="accept_event")
        accept.callback = self.accept_callback
        self.add_item(accept)
        deny = nextcord.ui.Button(label="Deny", style=nextcord.ButtonStyle.red, custom_id="deny_event")
        deny.callback = self.deny_callback
        self.add_item(deny)

    async def sticky2(self):
        channel = self.bot.get_channel(DONATE)
        try:
            id = collection.find_one({"_id": "sticky"})["response"]
            response = await channel.fetch_message(id)
            await response.delete()
        except:
            pass
        response = await channel.send(embed=MAIN_EMBED, view=View2())
        collection.update_one({"_id": "sticky"}, {"$set": {"response": response.id}}, upsert=True)

    async def accept_callback(self, interaction):
        async with self.lock:
            if not interaction.user.guild_permissions.manage_messages:
                return
            message_con = interaction.message.content
            try:
                donor = interaction.message.mentions[0]
            except:
                return
            if "donate" not in message_con:
                return
            elif not interaction.message.embeds:
                return
            elif interaction.message.author.id != 1291996619490984037:
                return
            reply = interaction.message.embeds[0].footer.text
            time = int(datetime.now().timestamp())
            descp = interaction.message.embeds[0].description
            event = interaction.message.embeds[0].title.split(" ")[3]
            descp = f"{descp}\n┊  🕛 ┊ <t:{time}:R>\n┊  🙂 ┊ **Host:** {interaction.user.mention}"
            new_embed = nextcord.Embed(title=f"┊ {GREEN_CHECK} ┊ Completed", description=descp, color=nextcord.Color.green())
            await interaction.message.edit(content=None, embed=new_embed, view=None)
            if interaction.channel.id == EVENT_QUEUE:
                channel = self.bot.get_channel(DONATE)
                try:
                    msg = await channel.fetch_message(int(reply))
                    await msg.reply(content=f"{donor.mention}, your donation for a(n) {event.lower()} is now being hosted.", mention_author=False)
                except:
                    pass
            elif interaction.channel.id == AUCTION_QUEUE:
                member = interaction.guild.get_member(donor.id)
                await member.add_roles(nextcord.utils.get(interaction.guild.roles, id=1205270486246883355))
                channel = self.bot.get_channel(AUCTION)
                await channel.send(content=f"{donor.mention} - an event manager has accepted your request for an auction. **__Please donate your item(s) here.__**")
                await asyncio.sleep(300)
                await member.remove_roles(nextcord.utils.get(interaction.guild.roles, id=1205270486246883355))

            try:
                await interaction.response.send_message(content=f"Accepted!", ephemeral=True)
            except:
                try:
                    await interaction.followup.send(content=f"Accepted!", ephemeral=True)
                except:
                    pass
            try:
                await interaction.delete_original_message()
            except:
                pass
            new_embed.title = f"┊ {GREEN_CHECK} ┊ Event/Giveaway/Heist Log"
            await self.bot.get_channel(LOG).send(embed=new_embed)
            await asyncio.sleep(5)
            await self.sticky2()

    async def deny_callback(self, interaction):
        async with self.lock:
            if not interaction.user.guild_permissions.manage_messages:
                return
            message_con = interaction.message.content
            if "donate" not in message_con:
                return
            elif not interaction.message.embeds:
                return
            elif interaction.message.author.id != 1291996619490984037:
                return
            donor = interaction.message.mentions[0]
            descp = interaction.message.embeds[0].description
            time = int(datetime.now().timestamp())
            descp = f"{descp}\n┊  🕛 ┊ <t:{time}:R>\n┊  🚫 ┊ **Denied By:** {interaction.user.mention}"
            if interaction.channel.id == EVENT_QUEUE:
                new_embed = nextcord.Embed(title=f"┊ {RED_X} ┊ Event Denied", description=descp, color=nextcord.Color.red())
                await interaction.message.edit(content=None, embed=new_embed, view=None)
            elif interaction.channel.id == AUCTION_QUEUE:
                new_embed = nextcord.Embed(title=f"┊ {RED_X} ┊ Auction Denied", description=descp, color=nextcord.Color.red())
                await interaction.message.edit(content=None, embed=new_embed, view=None)
            try:
                await donor.send(content=f"Your donation request has been denied by an event manager. For more information, click this [link]({interaction.message.jump_url}).")
            except:
                pass
            try:
                await interaction.response.send_message(content=f"Denied!", ephemeral=True)
            except:
                try:
                    await interaction.followup.send(content=f"Denied!", ephemeral=True)
                except:
                    pass
            try:
                await interaction.delete_original_message()
            except:
                pass
            await self.bot.get_channel(LOG).send(embed=new_embed)

class Donate(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.sticky_loop.start()
        self.bot.add_view(View(self.bot))
        self.bot.add_view(View2())
        print("Donate cog loaded")

    @commands.command(name="dse")
    async def sendsticky(self, ctx):
        await self.sticky()
        await ctx.message.delete()

    @tasks.loop(minutes=10)
    async def sticky_loop(self):
        channel = self.bot.get_channel(DONATE)
        try:
            messages = [message async for message in channel.history(limit=1)]
            message = messages[0]
            if message.author.id == self.bot.user.id:
                return
        except:
            pass
        await self.sticky()

    async def sticky(self):
        channel = self.bot.get_channel(DONATE)
        try:
            id = collection.find_one({"_id": "sticky"})["response"]
            response = await channel.fetch_message(id)
            await response.delete()
        except:
            pass
        try:
            response = await channel.send(embed=MAIN_EMBED, view=View2())
        except Exception as e:
            print(f"Error in sticky: {e}")
        collection.update_one({"_id": "sticky"}, {"$set": {"response": response.id}}, upsert=True)

    @commands.command(name="event")
    async def event(self, ctx):
        if ctx.channel.id != DONATE:
            return
        
        if len(ctx.message.content.split(" ")) == 1:
            await ctx.reply(content=f"Please provide information about what you're donating for.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        if "auction" in ctx.message.content.lower():
            arg = ctx.message.content.split(" ", 50)[2:]
            arg = " ".join(arg)
            await self.auction_donate(ctx, arg)
            return
        event = ctx.message.content.split(" ")[1]
        if len(ctx.message.content.split(" ")) <= 2:
            info = "None Specified."
        else:
            info = ctx.message.content.split(" ", 50)[2:]
            info = " ".join(info)
        descp = f"┊ 🎪 ┊ **Event:** {event}\n┊ 🏆 ┊ **Other Info:** {info}\n┊ 🔗 ┊ [Message Link]({ctx.message.jump_url})\n┊ 🙂 ┊ **Donor:** {ctx.author.mention}"
        embed = nextcord.Embed(title="┊ 📅 ┊ Event Pending", description=descp, color=nextcord.Color.blurple())
        con = f"{EMAN} - {ctx.author.mention} would like to donate for an event."
        try:
            embed.set_footer(text=f"{ctx.message.id}", icon_url=ctx.author.avatar.url)
        except:
            embed.set_footer(text=f"{ctx.message.id}")
        await self.bot.get_channel(EVENT_QUEUE).send(content=con, embed=embed, view=View(self.bot))
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content=f"Thank you for your donation {ctx.author.mention}, an event manager will be here shortly to host your event. __**Please make sure you have donated.**__", mention_author=False)
        await asyncio.sleep(5)
        await self.sticky()

    async def auction_donate(self, ctx, arg):
        if ctx.channel.id != DONATE:
            return
        if len(ctx.message.content.split(" ")) == 1:
            await ctx.reply(content=f"Please provide information about what you're donating for.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        user_roles = [role.id for role in ctx.author.roles]
        if 1205270486309670972 not in user_roles:
            await ctx.message.add_reaction(RED_X)
            await ctx.reply(content=f"You must be a 10M donator to donate for an auction.", mention_author=False)
            return
        descp = f"┊ 💰 ┊ **AUCTION**\n┊ 🏆 ┊ **Info:** {arg}\n┊ 🔗 ┊ [Message Link]({ctx.message.jump_url})\n┊ 🙂 ┊ **Donor:** {ctx.author.mention}"
        embed = nextcord.Embed(title="┊ 💰 ┊ Auction Pending", description=descp, color=nextcord.Color.blurple())
        con = f"{EMAN} - {ctx.author.mention} would like to donate for an auction."
        embed.set_footer(text=f"{ctx.message.id}", icon_url=ctx.author.avatar.url)
        await self.bot.get_channel(AUCTION_QUEUE).send(content=con, embed=embed, view=View(self.bot))
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content=f"Thank you for your donation {ctx.author.mention}, an event manager will be here shortly to host your auction. __**Please DO NOT donate your item(s) here.**__", mention_author=False)
        await asyncio.sleep(5)
        await self.sticky()

    @commands.command(name="heist")
    async def heist(self, ctx):
        if ctx.channel.id == 1205270487840596066:
            await self.heist_ping(ctx)
            return
        if ctx.channel.id != DONATE:
            return
        if len(ctx.message.content.split(" ")) == 1:
            await ctx.reply(content=f"Please provide information about what you're donating for.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        arg = ctx.message.content.split(" ", 50)[1:]
        arg = " ".join(arg)
        descp = f"┊ 💰 ┊ **HEIST**\n┊ 🏆 ┊ **Amount:** {arg}\n┊ 🔗 ┊ [Message Link]({ctx.message.jump_url})\n┊ 🙂 ┊ **Donor:** {ctx.author.mention}"
        embed = nextcord.Embed(title="┊ 💰 ┊ Heist Pending", description=descp, color=nextcord.Color.blurple())
        con = f"{ROOT} - {ctx.author.mention} would like to donate for a heist."
        embed.set_footer(text=f"{ctx.message.id}", icon_url=ctx.author.avatar.url)
        await self.bot.get_channel(EVENT_QUEUE).send(content=con, embed=embed, view=View(self.bot))
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content=f"Thank you for your donation {ctx.author.mention}, a pool manager will be here shortly to host your heist. __**Please make sure you have donated.**__", mention_author=False)
        await asyncio.sleep(5)
        await self.sticky()

    @commands.command(name="giveaway", aliases=["gaw"])
    async def giveaway(self, ctx):
        if ctx.channel.id != DONATE:
            return
        if len(ctx.message.content.split(" ")) == 1:
            await ctx.reply(content=f"Please provide information about what you're donating for.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        info = ctx.message.content.split(" ", 50)[1:]
        info = " ".join(info)
        descp = f"┊ 🎉 ┊ **GIVEAWAY**\n┊ 🏆 ┊ **Items:** {info}\n┊ 🔗 ┊ [Message Link]({ctx.message.jump_url})\n┊ 🙂 ┊ **Donor:** {ctx.author.mention}"
        embed = nextcord.Embed(title="┊ 💰 ┊ Giveaway Pending", description=descp, color=nextcord.Color.blurple())
        con = f"{GMAN} - {ctx.author.mention} would like to donate for an giveaway."
        embed.set_footer(text=f"{ctx.message.id}", icon_url=ctx.author.avatar.url)
        await self.bot.get_channel(EVENT_QUEUE).send(content=con, embed=embed, view=View(self.bot))
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content=f"Thank you for your donation {ctx.author.mention}, a giveaway manager will be here shortly to host your giveaway. __**Please make sure you have donated.**__", mention_author=False)
        await asyncio.sleep(5)
        await self.sticky()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != DONATE:
            return
        
        if message.content.startswith("!auction") or message.content.startswith("-auction") or message.content.startswith(".auction"):
            ctx = await self.bot.get_context(message)
            try:
                arg = message.content.split(" ", 20)[1:]
                arg = " ".join(arg)
                await self.auction_donate(ctx, arg)
            except IndexError:
                await message.reply("Please provide information about what you're auctioning!", mention_author=False)
            return
        
    async def heist_ping(self, ctx):
        if not ctx.author.guild_permissions.manage_messages:
            return
        ping = "<@&1205270486263795716>"
        content = ctx.message.content
        if " " in content:
            content = content.split(" ", 1)[1]
        else:
            content = ""
        await ctx.send(f"{ping} {content}")

def setup(bot):
    bot.add_cog(Donate(bot))
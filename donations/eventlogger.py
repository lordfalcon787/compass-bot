import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
from typing import Optional, List
from utils.mongo_connection import MongoConnection

DONATION_CHANNEL = 1386494501006217307
DANK_ID = 270904126974590976
GREEN_CHECK = "<:green_check2:1291173532432203816>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Donations"]
itemcollection = db["Items"]

class DonationCounter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Event Logger Cog Loaded.")

    @nextcord.slash_command(name="usesummerdonos", description="Use stuff from the Summer event.", guild_ids=[1205270486230110330])
    async def usesummerdonos(self, interaction: nextcord.Interaction,
                           quantity: str = SlashOption(description="The quantity of the item to use or coins to use."),
                           item: Optional[str] = SlashOption(description="The item to use.", autocomplete=True)):
        await interaction.response.defer(ephemeral=False)
        manager = 1375928800046616766
        roles = [role.id for role in interaction.user.roles]
        if manager not in roles and not interaction.user.guild_permissions.administrator:
            await interaction.send(content="You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "summer_donations"})
        if not doc:
            await interaction.send(content="No donations have been made yet.", ephemeral=False)
            return
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(quantity[:-1])
                multiplier = multipliers[quantity[-1]]
                quantity = int(numeric_part * multiplier)
            except ValueError:
                await interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=False)
                return
        else:
            if ',' in quantity:
                quantity = quantity.replace(',', '')
            try:
                quantity = int(quantity)
            except ValueError:
                await interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=False)
                return
        quan = quantity
        if item:
            if item not in doc:
                await interaction.send(content="That item does not exist or has not been donated yet.", ephemeral=False)
                return
            if doc[item] < quan:
                await interaction.send(content="That item does not have that many donations.", ephemeral=False)
                return
            doc[item] = doc[item] - quan
            collection.update_one({"_id": "summer_donations"}, {"$set": doc}, upsert=True)
            await interaction.send(content=f"Updated database. `{quan:,}x` {item} were used.", ephemeral=False)
        else:
            if doc["coins"] < quan:
                await interaction.send(content="There are not enough coins to use.", ephemeral=False)
                return
            doc["coins"] -= quan
            collection.update_one({"_id": "summer_donations"}, {"$set": doc}, upsert=True)
            await interaction.send(content=f"Updated database. `{quan:,}` coins were used.", ephemeral=False)
        
    @commands.command(name="summerdonos", aliases=["sdonos"])
    async def summerdonos(self, ctx):
        try:
            doc = collection.find_one({"_id": "summer_donations"})
            if not doc:
                collection.insert_one({"_id": "summer_donations", "coins": 0})
                doc = collection.find_one({"_id": "summer_donations"})
            coins = doc["coins"]
            desc = f"__**Coins:**__  ⏣ {coins:,}\n**Items:**"
            doc.pop("coins")
            doc.pop("_id")
            desc_pages = []
            total = 0
            items_dict = {}
            coins_desc = f"__**Coins:**__  ⏣ {coins:,}\n\n__**Items:**__"
            current_desc = coins_desc
            total += coins
            items_added = 0
            for item in doc:
                value = itemcollection.find_one({"_id": item})
                if not value:
                    value = "Unknown"
                else:
                    value = value["price"]
                    value = int(value)
                    value = value * int(doc[item])
                    total += value
                    value = int(value)
                items_dict[item] = {"value": value, "amount": doc[item]}
            
            known_items = {k: v for k, v in items_dict.items() if v["value"] != "Unknown"}
            unknown_items = {k: v for k, v in items_dict.items() if v["value"] == "Unknown"}
            known_items = dict(sorted(known_items.items(), key=lambda x: x[1]["value"], reverse=True))
            items_dict = {**known_items, **unknown_items}
            
            for item in items_dict:
                value = items_dict[item]["value"]
                if value != "Unknown":
                    value = f"⏣ {value:,}"
                else:
                    value = "Unknown"
                if items_dict[item]["amount"] > 0:
                    current_desc = f"{current_desc}\n`{items_dict[item]['amount']}x` {item} - {value}"
                    items_added += 1

                if items_added >= 15:
                    desc_pages.append(current_desc)
                    current_desc = coins_desc
                    items_added = 0
            
            if items_added > 0:
                desc_pages.append(current_desc)
            
            if not desc_pages:
                desc_pages.append(coins_desc)

            embeds = []
            for i, desc in enumerate(desc_pages):
                desc = f"**__Total Donation Value:__** ⏣ {total:,}\n\n{desc}"
                embed = nextcord.Embed(title="RC Summer Donations", description=desc, color=65280)
                embed.set_thumbnail(url="https://i.imgur.com/cNIVuoA.jpeg")
                embed.set_footer(text=f"Robbing Central - Page {i + 1}/{len(desc_pages)}", icon_url=self.bot.user.display_avatar.url)
                embeds.append(embed)

            view = nextcord.ui.View()
            
            left_button = nextcord.ui.Button(emoji="<a:arrow_left:1316079524710191156>", custom_id="left_arrow", disabled=True)
            view.add_item(left_button)

            right_button = nextcord.ui.Button(emoji="<a:arrow_right:1316079547124285610>", custom_id="right_arrow")
            view.add_item(right_button)

            if len(embeds) == 1:
                right_button.disabled = True

            await ctx.reply(embed=embeds[0], view=view, mention_author=False)

            current_page = 0

            async def button_left_callback(interaction):
                nonlocal current_page
                if current_page > 0:
                    current_page -= 1

                left_button.disabled = (current_page == 0)
                right_button.disabled = (current_page == len(embeds) - 1)

                await interaction.response.edit_message(embed=embeds[current_page], view=view)

            async def button_right_callback(interaction):
                nonlocal current_page
                if current_page < len(embeds) - 1:
                        current_page += 1
                
                left_button.disabled = (current_page == 0)
                right_button.disabled = (current_page == len(embeds) - 1)

                await interaction.response.edit_message(embed=embeds[current_page], view=view)

            left_button.callback = button_left_callback
            right_button.callback = button_right_callback
        except Exception as e:
            await ctx.reply(f"An error occurred: {str(e)}", mention_author=False)

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id != DONATION_CHANNEL:
            return
        
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author.id != DANK_ID:
            return
        elif not message.embeds:
            return
        elif not message.embeds[0].description:
            return
        elif "successfully donated" not in message.embeds[0].description.lower():
            return
        
        descp = message.embeds[0].description

        if "⏣" in descp:
            amount = descp.split("⏣")[1]
            amount = amount.replace("*", "")
            amount = amount.replace(",", "")
            amount = int(amount)
            collection.update_one({"_id": "summer_donations"}, {"$inc": {"coins": amount}}, upsert=True)
            await message.add_reaction(GREEN_CHECK)
        else:
            amount = descp.split("donated ")[1]
            amount = amount.replace("*", "")
            first = amount.split("<")[0]
            second = amount.split("> ")[1]
            amount = f"{first} {second}"
            first = first.replace(" ", "")
            first = first.replace(",", "")
            first = int(first)
            collection.update_one({"_id": "summer_donations"}, {"$inc": {second: first}}, upsert=True)
            await message.add_reaction(GREEN_CHECK)

    async def get_choices(self, interaction, current: str) -> List[str]:
        prefix_query = {"_id": {"$regex": f"^{current}", "$options": "i"}}
        choices = [doc["_id"] for doc in itemcollection.find(prefix_query).limit(25)]
        if not choices:
            word_query = {"_id": {"$regex": f"\\b{current}", "$options": "i"}}
            choices = [doc["_id"] for doc in itemcollection.find(word_query).limit(25)]
            
        return choices
    
    @commands.command(name="addsdonos", aliases=["asdonos"])
    async def addsdonos(self, ctx):
        doc = collection.find_one({"_id": "summer_donations"})
        if not doc:
            collection.insert_one({"_id": "summer_donations", "coins": 0})
            doc = collection.find_one({"_id": "summer_donations"})
        split = ctx.message.content.split(" ")
        if len(split) < 2:
            await ctx.reply("Please provide an item and amount.", mention_author=False)
            return
        if len(split) == 2:
            collection.update_one({"_id": "summer_donations"}, {"$inc": {"coins": int(split[1])}}, upsert=True)
            await ctx.reply(f"Added {split[1]} coins to the database.", mention_author=False)
            return
        if len(split) == 3:
            collection.update_one({"_id": "summer_donations"}, {"$inc": {split[2]: int(split[1])}}, upsert=True)
            await ctx.reply(f"Added {split[1]} {split[2]} to the database.", mention_author=False)
            return
    
    @usesummerdonos.on_autocomplete("item")
    async def autocomplete_handler(self, interaction: nextcord.Interaction, current: str):
        try:
            choices = await self.get_choices(interaction, current)
            await interaction.response.send_autocomplete(choices)
        except:
            try:
                await interaction.response.send_autocomplete([])
            except:
                pass

def setup(bot):
    bot.add_cog(DonationCounter(bot))
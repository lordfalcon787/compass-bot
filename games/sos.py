import nextcord
from nextcord.ext import commands, application_checks
from typing import Optional, List
import asyncio
import random
from utils.mongo_connection import MongoConnection

TESTING_GUILD_ID = 1234605482937684059
RC_ID = 1205270486230110330
RC_AUCTION_QUEUE = 1267530934723281009
RC_EVENT_QUEUE = 1267527896218468412
EVENT_QUEUE = 1266257466677792768
AUCTION_QUEUE = 1267355852856229918
RC_ICON = "https://i.imgur.com/K5L7kxl.png"
RC_BANNER = "https://i.imgur.com/kL6BSmK.jpeg"
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Split or Steal"]
item_collection = db["Items"]
configuration = db["Configuration"]

IMAGE = "https://cdn.discordapp.com/emojis/994010029218877572.gif"

class JoinButton(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Join", style=nextcord.ButtonStyle.primary, custom_id="join_sos")
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": interaction.message.id})
        if interaction.user.id in doc["Participants"]:
            await interaction.response.send_message("You have already joined this event!", ephemeral=True)
            return 
        
        collection.update_one({"_id": interaction.message.id}, {"$push": {"Participants": interaction.user.id}})
        try:
            await interaction.response.send_message("You have joined the event!", ephemeral=True)
        except:
            pass

class SplitOrStealButton(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        split_button = nextcord.ui.Button(label="Split", style=nextcord.ButtonStyle.green, custom_id="split_sos")
        split_button.callback = self.split_callback
        self.add_item(split_button)

        steal_button = nextcord.ui.Button(label="Steal", style=nextcord.ButtonStyle.red, custom_id="steal_sos")
        steal_button.callback = self.steal_callback
        self.add_item(steal_button)

    async def split_callback(self, interaction: nextcord.Interaction):
        await self.handle_choice(interaction, "SPLIT")

    async def steal_callback(self, interaction: nextcord.Interaction):
        await self.handle_choice(interaction, "STEAL")

    async def handle_choice(self, interaction: nextcord.Interaction, choice: str):
        doc = collection.find_one({"_id": interaction.message.id})
        if interaction.user.id not in doc["Winners"]:
            await interaction.response.send_message("You are not a participant in this event!", ephemeral=True)
            return
        collection.update_one({"_id": interaction.message.id}, {"$set": {f"{interaction.user.id}_choice": choice}})
        await interaction.response.send_message(f"You have selected **{choice.lower()}**!", ephemeral=True)

class SOS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(JoinButton())
        self.bot.add_view(SplitOrStealButton())
        print("SOS cog is ready")

    @nextcord.slash_command(description="Run a split or steal event.")
    @application_checks.guild_only()
    async def sos(self, interaction: nextcord.Interaction,
                  donor: nextcord.Member = nextcord.SlashOption(description="The donor of the event."),
                  quantity: str = nextcord.SlashOption(description="The amount of coins/items."),
                  item: Optional[str] = nextcord.SlashOption(description="The item to be donated.", autocomplete=True)):
        
        DONOR = donor.id
        items = item
        amount = quantity

        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to run this command!", ephemeral=True)
            return

        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        quantity = amount.lower()
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(amount[:-1])
                multiplier = multipliers[amount[-1]]
                amount = int(numeric_part * multiplier)
            except ValueError:
                await interaction.response.send_message("Invalid quantity format. Please use a number followed by k, m, b, or t.", ephemeral=True)
                return
        else:
            if ',' in amount:
                amount = amount.replace(',', '')
            try:
                amount = int(amount)
            except ValueError:
                await interaction.response.send_message("Invalid quantity. Please enter a number.", ephemeral=True)
                return
        
        quantity = amount
        QUANTITY = quantity

        if item is None:
            items = "None"

        prize = f"{quantity:,}"

        if items != "None":
            prize = f"{quantity:,} {items}"
    
        embed = nextcord.Embed(title="Split or Steal", description=f"> **Donor:** <@{DONOR}>\n> **Prize:** {prize} \n\n You have 90 seconds to join the Split or Steal by clicking the button below. \n \n Two people will be selected. If both select split, you split the prize - if one steals and the other splits, the person who steals wins all. If you both steal none of you get the prize. Selecting nothing means split.", color=nextcord.Color.blurple())
        embed.set_thumbnail(url=IMAGE)
        embed.set_footer(text="You have 90 seconds to join the event.", icon_url=RC_ICON)
        await interaction.response.send_message("Event created!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=JoinButton())
        new_doc = {
            "_id": msg.id,
            "Donor": DONOR,
            "Quantity": QUANTITY,
            "Item": items,
            "Participants": [],
            "Winners": [],
            "Host": interaction.user.id
        }
        collection.insert_one(new_doc)

        await asyncio.sleep(90)
        doc = collection.find_one({"_id": msg.id})
        message = await msg.channel.fetch_message(msg.id)
        if len(doc["Participants"]) == 0 or len(doc["Participants"]) == 1:
            await msg.edit(embed=embed, view=None)
            await message.reply(content="Not enough participants to run the event!")
            collection.delete_one({"_id": msg.id})
            return
        
        participants = doc["Participants"]
        winners = random.sample(participants, 2) if len(participants) >= 2 else participants
        collection.update_one({"_id": msg.id}, {"$set": {"Winners": winners}})
        winner1 = winners[0]
        winner2 = winners[1]
        new_embed = nextcord.Embed(title="Split or Steal", description=f"> **Donor:** <@{DONOR}>\n> **Prize:** {prize} \n\n You have 1 minute to decide whether you would like to split or steal. \n \n If both select split, you split the prize - if one steals and the other splits, the person who steals wins all. If you both steal none of you get the prize. Selecting nothing means split.", color=nextcord.Color.blurple())
        new_embed.set_thumbnail(url=IMAGE)
        collection.update_one(
            {"_id": msg.id}, 
            {
                "$set": {
                    "Winners": winners,
                    f"{winner1}_choice": "NOTHING",
                    f"{winner2}_choice": "NOTHING"
                }
            }
        )
        doc = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        player_role_doc = doc["player_role"]
        player_role_id = player_role_doc.get(guild_id)
        if player_role_id:
            player_role = interaction.guild.get_role(player_role_id)
            w1_mem = interaction.guild.get_member(winner1)
            w2_mem = interaction.guild.get_member(winner2)
            try:
                await w1_mem.add_roles(player_role)
                await w2_mem.add_roles(player_role)
            except:
                pass

        await msg.edit(content=f"<@{winner1}> <@{winner2}>", embed=new_embed, view=SplitOrStealButton())
        await message.reply(content=f"<@{winner1}>, <@{winner2}>")

        await asyncio.sleep(60)
        if player_role_id:
            try:
                player_role = interaction.guild.get_role(player_role_id)
                await w1_mem.remove_roles(player_role)
                await w2_mem.remove_roles(player_role)
            except:
                pass
        doc = collection.find_one({"_id": msg.id})
        host = doc["Host"]
        quantity_split = quantity / 2
        winner1_choice = doc[f"{winner1}_choice"]
        winner2_choice = doc[f"{winner2}_choice"]
        winner1_choice = winner1_choice.upper()
        winner2_choice = winner2_choice.upper()
        embed = nextcord.Embed(title="Split or Steal", description=f"> **Donor:** <@{DONOR}>\n> **Prize:** {prize} \n\n Two people will be selected. If both select split, you split the prize - if one steals and the other splits, the person who steals wins all. If you both steal none of you get the prize. Selecting nothing means split. \n\n **RESULTS:** \n\n- <@{winner1}> chose **{winner1_choice}** \n- <@{winner2}> chose **{winner2_choice}**", color=nextcord.Color.blurple())
        await msg.edit(embed=embed, view=None)
        default_reply = f"<@{host}>"
        payout_msg = ""
        if winner1_choice == "STEAL" and winner2_choice == "STEAL":
            default_reply = f"<@{host}> - No one won."
        elif winner1_choice == "SPLIT" and winner2_choice == "SPLIT":
            default_reply = f"<@{host}> - Both participants split the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner1} {winner2} quantity:{round(quantity_split):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        elif winner1_choice == "SPLIT" and winner2_choice == "STEAL":
            default_reply = f"<@{host}> - <@{winner2}> stole the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner2} quantity:{round(quantity):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        elif winner1_choice == "STEAL" and winner2_choice == "SPLIT":
            default_reply = f"<@{host}> - <@{winner1}> stole the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner1} quantity:{round(quantity):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        elif winner1_choice == "NOTHING" and winner2_choice == "NOTHING":
            default_reply = f"<@{host}> - Both participants split the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner1} {winner2} quantity:{round(quantity_split):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        elif winner1_choice == "NOTHING" and winner2_choice == "STEAL":
            default_reply = f"<@{host}> - <@{winner2}> stole the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner2} quantity:{round(quantity):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        elif winner1_choice == "STEAL" and winner2_choice == "NOTHING":
            default_reply = f"<@{host}> - <@{winner1}> stole the prize!"
            payout_msg = f"/payout create event:SOS message_id:{msg.id} winners_list:{winner1} quantity:{round(quantity):,}"
            if items != "None":
                payout_msg += f" item:{items}"
        await message.reply(content=default_reply)
        if payout_msg != "":
            await interaction.followup.send(content=f"{payout_msg}\n```{payout_msg}```", ephemeral=True)
        collection.delete_one({"_id": msg.id})

    async def get_choices(self, interaction, current: str) -> List[str]:
        prefix_query = {"_id": {"$regex": f"^{current}", "$options": "i"}}
        choices = [doc["_id"] for doc in item_collection.find(prefix_query).limit(25)]
        if not choices:
            word_query = {"_id": {"$regex": f"\\b{current}", "$options": "i"}}
            choices = [doc["_id"] for doc in item_collection.find(word_query).limit(25)]
            
        return choices

    @sos.on_autocomplete("item")
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
    bot.add_cog(SOS(bot))

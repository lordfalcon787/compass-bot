import nextcord
import time
import asyncio
import re
import aiohttp
from nextcord.ext import commands, tasks, application_checks
from nextcord import SlashOption

from typing import Optional, List
from datetime import datetime

from utils.mongo_connection import MongoConnection


mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = mongo.get_collection("Payouts")
queuecollection = mongo.get_collection("Payout Queue")
itemcollection = mongo.get_collection("Items")
collec = mongo.get_collection("Misc")
backup = mongo.get_collection("Backup Items")
misc = mongo.get_collection("Misc")
configuration = mongo.get_collection("Configuration")

loading_emoji = "<a:loading_animation:1218134049780928584>"

CLAIM = 1205270487643459616
QUEUE = 1205270487643459617
RC_ID = 1205270486230110330
ROOT_ID = 1206299567520354317
PAYOUT = 1205270487643459618

PAID = "<:rc_paid:1304668330468053023>"
DOT = "<a:golddot:1303833388410601522>"
GREEN_CHECK = "<:green_check:1218286675508199434>"

DICT = {487328045275938828: "gartic", 807692666107985941: "giveaway",758999095070687284: "mafia", 511786918783090688: "mafia", 693167035068317736: "rumble", 675996677366218774: "hangry"}

class EditPrizeModal(nextcord.ui.Modal):
    def __init__(self, bot, interaction):
        super().__init__(
            "Edit Prize",
            timeout=300,
        )

        self.event_name = nextcord.ui.TextInput(
            label="New Prize",
            placeholder="Enter the Prize",
            min_length=1,
            max_length=50,
            required=True,
        )
        self.bot = bot
        self.interaction = interaction
        self.add_item(self.event_name)

    async def callback(self, modal_interaction: nextcord.Interaction):
        await modal_interaction.response.defer(ephemeral=True)
        old_answer = self.event_name.value
        answer = old_answer.split(" ")

        async def confirm_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal msg
            nonlocal item
            nonlocal quantity
            nonlocal was_confirmed
            was_confirmed = True
            embedd = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Updating database to new prize...")
            await msg.edit(embed=embedd, view=None)
            message = self.interaction.message
            queue_msg_button = None
            for row in message.components:
                for component in row.children:
                    if component.label == "Queue Message":
                        queue_msg_button = component
                        break
                if queue_msg_button:
                    break
            if queue_msg_button is None:
                await msg.edit(content="Could not find Queue Message button", embed=None, view=None)
                return
            queue_msg_url = queue_msg_button.url
            doc = collection.find_one({"queuemsg": queue_msg_url})
            if doc is None:
                await msg.edit(content="Could not find payout in database, it might have been paid already.", embed=None, view=None) 
                return
            if item:
                value = itemcollection.find_one({"_id": item})
                if not value:
                    value = 0
                else:
                    value = value["price"]
                value = int(value * quantity)
                collection.update_one({"_id": doc["_id"]}, {"$set": {"prize": quantity, "value": value, "item": item}})
            else:
                value = int(quantity)
                collection.update_one({"_id": doc["_id"]}, {"$set": {"prize": quantity, "value": value, "item": None}})
            config = configuration.find_one({"_id": "config"})
            queue = config[f"queue"]
            queue = queue[f"{interaction.guild.id}"]
            channel = self.bot.get_channel(queue)
            queue_msg = await channel.fetch_message(int(queue_msg_url.split("/")[6]))
            embed = queue_msg.embeds[0]
            embed_footer = embed.footer.text
            queuer = embed_footer.split(" ")[2]
            embed.set_footer(text=f"Queued by {queuer} and edited by {interaction.user.name}")
            prize_info_index = None
            for i, field in enumerate(embed.fields):
                if field.name == "Prize Info":
                    prize_info_index = i
                    break
            if prize_info_index is not None:
                if item:
                    embed.set_field_at(prize_info_index, name="Prize Info", value=f"{DOT} **Won:** `{quantity:,}x` {item}\n{DOT} **Value:** `⏣ {value:,}`")
                else:
                    embed.set_field_at(prize_info_index, name="Prize Info", value=f"{DOT} **Won:** `⏣ {quantity:,}`")
            else:
                if item:
                    embed.add_field(name="Prize Info", value=f"{DOT} **Won:** `{quantity:,}x` {item}\n{DOT} **Value:** `⏣ {value:,}`")
                else:
                    embed.add_field(name="Prize Info", value=f"{DOT} **Won:** `⏣ {quantity:,}`")
            await queue_msg.edit(embed=embed)
            claim_msg = self.interaction.message
            embed = claim_msg.embeds[0]
            if item:
                embed.set_field_at(prize_info_index, name="Prize Info", value=f"{DOT} **Won:** `{quantity:,}x` {item}\n{DOT} **Value:** `⏣ {value:,}`")
            else:
                embed.set_field_at(prize_info_index, name="Prize Info", value=f"{DOT} **Won:** `⏣ {quantity:,}`")
            embed.set_footer(text=f"Queued by {queuer} and edited by {interaction.user.name}")
            await claim_msg.edit(embed=embed)
            embedd.description = f"<:green_check:1218286675508199434> | Prize has been updated successfully."
            embedd.color = 65280
            await msg.edit(embed=embedd, view=None)

        async def cancel_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal msg
            nonlocal was_confirmed
            was_confirmed = True
            await msg.edit(content="Cancelled payout process.", embed=None, view=None)


        if len(answer) == 1:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return
            confirmation_embed = nextcord.Embed(title="Confirm Edit", description=f"Are you sure you want to edit the prize to {quantity:,}?")
            confirmation_embed.add_field(name="New Prize", value=f"{quantity:,}")
            view = nextcord.ui.View()
            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            item = None
            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(10)
            if not was_confirmed:
                await msg.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)
        else:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return
            item_choice = old_answer.replace(f"{answer[0]} ", "")
            item_collection = list(itemcollection.find())
            item_choice = item_choice.lower()
            closest_item = None

            for item in item_collection:
                item_name = item["_id"].lower()
                if item_name == item_choice:
                    closest_item = item
                    break
                
                try:
                    if len(item_choice.split(" ")) == 2 and len(item_name.split(" ")[0] == item_choice.split(" ")[0] and item_name.split(" ")[1] == item_choice.split(" ")[1]):
                        closest_item = item
                        break
                except:
                    pass

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    try:
                        if all(word in item_name for word in item_choice.split()):
                            closest_item = item
                            break
                    except:
                        pass

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    try:
                        if item_choice.split(" ")[0] in item_name:
                            closest_item = item
                            break
                    except:
                        pass

            if not closest_item and len(item_choice.split(" ")) > 1:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    try:
                        if item_choice.split(" ")[1] in item_name:
                            closest_item = item
                            break
                    except:
                        pass

            if closest_item:
                item = closest_item["_id"]
            else:
                await msg.edit(content="No matching item found. Please try again.")
                return
            
            confirmation_embed = nextcord.Embed(title="Confirm Edit", description=f"Are you sure you want to edit the prize to {quantity:,} {item}?")
            confirmation_embed.add_field(name="New Prize", value=f"{quantity:,} {item}")
            view = nextcord.ui.View()
            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(10)
            if not was_confirmed:
                await msg.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)


    def calculate_match_score(self, item_name, user_input):
        item_name = item_name.lower()
        user_input = user_input.lower()
        
        if item_name == user_input:
            return 0
            
        item_words = item_name.split()
        input_words = user_input.split()
        
        all_words_match = all(any(input_word in item_word or item_word in input_word
                                for item_word in item_words)
                            for input_word in input_words)
                            
        if all_words_match:
            return 1 + abs(len(item_name) - len(user_input)) / 100
            
        max_len = max(len(item_name), len(user_input))
        return 100 + sum(1 for i in range(max_len) if i >= len(item_name)
                        or i >= len(user_input)
                        or item_name[i] != user_input[i])       

class OverrideView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        override = nextcord.ui.Button(label="Override", style=nextcord.ButtonStyle.blurple, custom_id="override", emoji="🛫")
        override.callback = self.override_callback
        self.add_item(override)

    async def override_callback(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            await interaction.response.send_message(content="No payout process is currently active.", ephemeral=True)
            return
        collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})
        await interaction.response.send_message(content="Payout process has been overridden. Run </payout express:1307554548327518280> to start a new payout proccess.", ephemeral=True)

class QueuedPayoutsView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class QueuedView(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

        edit_prize = nextcord.ui.Button(label="Edit Prize", style=nextcord.ButtonStyle.blurple, custom_id="edit_prize", emoji="📝")
        edit_prize.callback = self.edit_prize_callback
        self.add_item(edit_prize)
    
    async def edit_prize_callback(self, interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        try:
            await interaction.response.send_modal(EditPrizeModal(self.bot, interaction))
        except:
            return

class RejectWithReasonModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Reject With Reason",
            timeout=300,
        )

        self.reason = nextcord.ui.TextInput(
            label="Reason",
            placeholder="Enter the reason for rejecting the payout",
            min_length=1,
            max_length=75,
            required=True,
        )
        self.add_item(self.reason)

    async def callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        reason = self.reason.value
        doc = collection.find_one({"_id": interaction.message.id})
        if doc is None:
            return
        collection.delete_one({"_id": interaction.message.id})
        embed = interaction.message.embeds[0]
        embed.title = "Payout Rejected"
        embed.color = 16711680
        embed.add_field(name="Rejected By", value=f"{interaction.user.mention}", inline=True)
        embed.add_field(name="Reason", value=f"`{reason}`", inline=False)
        link = doc["link"]
        view = QueuedPayoutsView()
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{link}", emoji="🔗"))
        await interaction.message.edit(content=None, embed=embed, view=view)
        await interaction.send(content=f"This payout has been rejected for reason: `{reason}`", ephemeral=True)
        
class QueueView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        reject_button = nextcord.ui.Button(label="❌ Reject", style=nextcord.ButtonStyle.red, custom_id="reject_callback")
        reject_button.callback = self.reject_callback
        self.add_item(reject_button)
        reject_with_reason_button = nextcord.ui.Button(label="❌ Reject With Reason", style=nextcord.ButtonStyle.red, custom_id="reject_with_reason_callback")
        reject_with_reason_button.callback = self.reject_with_reason_callback
        self.add_item(reject_with_reason_button)

    async def reject_callback(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": interaction.message.id})
        if doc is None:
            return
        roles = [role.id for role in interaction.user.roles]
        config = configuration.find_one({"_id": "config"})
        root = config[f"root"]
        root = root[f"{interaction.guild.id}"]
        if root not in roles:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        collection.delete_one({"_id": interaction.message.id})
        embed = interaction.message.embeds[0]
        embed.title = "Payout Rejected"
        embed.color = 16711680
        embed.add_field(name="Rejected By", value=f"{interaction.user.mention}", inline=True)
        link = doc["link"]
        view = QueuedPayoutsView()
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{link}", emoji="🔗"))
        await interaction.message.edit(content=None, embed=embed, view=view)
        await interaction.response.send_message(content="This payout has been rejected.", ephemeral=True)
        collec.update_one({"_id": "payout_stats"}, {"$inc": {"rejected": 1}})

    async def reject_with_reason_callback(self, interaction: nextcord.Interaction):
        roles = [role.id for role in interaction.user.roles]
        config = configuration.find_one({"_id": "config"})
        root = config[f"root"]
        root = root[f"{interaction.guild.id}"]
        if root not in roles:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.send_modal(RejectWithReasonModal())
        
class View(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        claim_button = nextcord.ui.Button(label="Claim", style=nextcord.ButtonStyle.green, custom_id="claim_callback")
        claim_button.callback = self.claim_callback
        cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.red, custom_id="cancel_callback")
        cancel_button.callback = self.cancel_callback
        self.add_item(claim_button)
        self.add_item(cancel_button)
    
    async def claim_callback(self, interaction: nextcord.Interaction):
        doc = queuecollection.find_one({"_id": interaction.message.id})
        if doc is None:
            return
        if doc["winner"] != interaction.user.id:
            await interaction.response.send_message(content="You are not the winner of this payout.", ephemeral=True)
            return
        embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Claiming payout...")
        embed.set_footer(text=f"This should take around a second.")
        try:
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except:
            return
        embed = interaction.message.embeds[0]
        embed.timestamp = datetime.now()
        link = doc["link"]
        view = QueueView()
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{link}", emoji="🔗"))
        config = configuration.find_one({"_id": "config"})
        queue = config[f"queue"]
        queue = queue[f"{interaction.guild.id}"]
        msg = await self.bot.get_channel(queue).send(embed=embed, view=view)
        link = doc["link"]
        view = QueuedView(self.bot)
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{link}", emoji="🔗"))
        view.add_item(nextcord.ui.Button(label="Queue Message", url=f"{msg.jump_url}", emoji="🔗"))
        await interaction.message.edit(content=None, view=view)
        embed = nextcord.Embed(description=f"<:green_check:1218286675508199434> | This payout has been claimed successfully.", color=65280)
        embed.set_footer(text=f"You will be paid out within 48 hours.")
        doc["queuemsg"] = msg.jump_url
        doc["_id"] = msg.id
        doc["claimed_at"] = int(datetime.utcnow().timestamp())
        collection.insert_one(doc)
        queuecollection.delete_one({"_id": interaction.message.id})
        await interaction.edit_original_message(embed=embed)
        collec.update_one({"_id": f"payout_stats_{interaction.guild.id}"}, {"$inc": {"claimed": doc["value"], "claimed_amt": 1}})
    
    async def cancel_callback(self, interaction: nextcord.Interaction):
        try:
            doc = queuecollection.find_one({"_id": interaction.message.id})
            host = doc["host"]
            winner = doc["winner"]
        except:
            return
        slice = [host, winner]
        if interaction.user.id not in slice and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        queuecollection.delete_one({"_id": interaction.message.id})
        embed = interaction.message.embeds[0]
        embed.title = "Payout Cancelled"
        embed.color = 16711680
        link = doc["link"]
        view = QueuedPayoutsView()
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{link}", emoji="🔗"))
        await interaction.message.edit(content=None, embed=embed, view=view)
        await interaction.response.send_message(content="This payout has been cancelled successfully.", ephemeral=True)
    
class PayoutState:
    _instance = None
    
    def __init__(self):
        self.last_interactions = {}
        self.last_responses = {}
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = PayoutState()
        return cls._instance

class PayoutView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class ViewPayout(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        self.state = PayoutState.get_instance()
        skip = nextcord.ui.Button(label="Skip", style=nextcord.ButtonStyle.primary, custom_id="skip", emoji="⏭️")
        skip.callback = self.skip_callback
        self.add_item(skip)
        
        exit = nextcord.ui.Button(label="Exit", style=nextcord.ButtonStyle.success, custom_id="exit", emoji="<:Exit:1315225802266382416>")
        exit.callback = self.exit_callback
        self.add_item(exit)
        
        reject = nextcord.ui.Button(label="Reject", style=nextcord.ButtonStyle.danger, custom_id="reject", emoji="❌")
        reject.callback = self.reject_callback
        self.add_item(reject)

    async def skip_callback(self, interaction):
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["payouter"] != interaction.user.id:
            return
        id = doc["current_id"]
        collection.update_one({"_id": f"current_payout_{interaction.guild.id}"}, {"$pull": {"payout_slice": id}})
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if len(doc["payout_slice"]) == 0:
            await interaction.send("All payouts have been completed.", ephemeral=True)
            collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})
            return
        new_id = doc["payout_slice"][0]
        new_doc = collection.find_one({"_id": new_id})
        prize = new_doc["prize"]
        item = new_doc["item"]
        usr = new_doc["winner"]
        current = doc["current"] + 1
        if item:
            prize = f"{prize} {item}"
        time = int(datetime.utcnow().timestamp())
        collection.update_one({"_id": f"current_payout_{interaction.guild.id}"}, {"$set": {"user": usr, "prize": prize, "current_id": new_id, "time": time, "current": current}})
        if item:
            command = f"/serverevents payout user:{usr} quantity:{prize.split(' ')[0]} item:{item}"
        else:
            command = f"/serverevents payout user:{usr} quantity:{prize}"
        if "claimed_at" in new_doc.keys():
            claimed = f"<t:{new_doc['claimed_at']}:R>"
        else:
            claimed = "None"
        guild_name = interaction.guild.name
        if doc["platform"] == 2:
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Press the below buttons to execute:**\n- skip: skip this payout\n- reject: reject this payout\n- exit: exit the payout proccess\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
            embed.add_field(name="Easy Copy Version", value=f"```{command}```", inline=False)
        else:
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
        embed.add_field(name="Command", value=command, inline=False)
        embed.set_footer(text=f"Payout {current}/{doc['amount']}")
        if doc["platform"] == 1:
            content = command
        else:
            content = None
        view = ViewPayout(self.bot)
        view.add_item(nextcord.ui.Button(label="Events Message", url=f"{new_doc['link']}", emoji="🔗"))
        try:
            await self.state.last_responses[interaction.guild.id].delete()
        except:
            pass
        self.state.last_responses[interaction.guild.id] = await interaction.send(content=content, embed=embed, ephemeral=True, view=view)
        await asyncio.sleep(60)
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["time"] == time:
            await interaction.send("Inactivity detected. Exiting payout process.", ephemeral=True)
            await self.state.last_responses[interaction.guild.id].delete()
            collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})
        

    async def exit_callback(self, interaction):
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["payouter"] != interaction.user.id:
            return
        collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})
        try:
            await self.state.last_responses[interaction.guild.id].delete()
        except:
            pass
        await interaction.send("Payout process has been exited.", ephemeral=True)
    
    async def reject_callback(self, interaction):
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["payouter"] != interaction.user.id:
            return
        id = doc["current_id"]
        current = doc["current"] + 1
        collection.update_one({"_id": f"current_payout_{interaction.guild.id}"}, {"$pull": {"payout_slice": id}})
        other_doc = collection.find_one({"_id": id})
        collection.delete_one({"_id": id})
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})


        guild_name = interaction.guild.name
        config = configuration.find_one({"_id": "config"})
        claim = config[f"claim"]
        claim = claim[f"{interaction.guild.id}"]
        queue = config[f"queue"]
        queue = queue[f"{interaction.guild.id}"]
        if len(doc["payout_slice"]) == 0:
            await interaction.send("All payouts have been completed.", ephemeral=True)
            collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})
            collection.delete_one({"_id": id})
            queue_msg = other_doc["queuemsg"].split("/")[6]
            channel = self.bot.get_channel(queue)
            queue_msg = await channel.fetch_message(int(queue_msg))
            embed = queue_msg.embeds[0]
            embed.title = "Payout Rejected"
            embed.color = 16711680
            embed.add_field(name="Rejected By", value=f"{interaction.user.mention}", inline=True)
            await queue_msg.edit(embed=embed, view=None)
            return
        new_id = doc["payout_slice"][0]
        new_doc = collection.find_one({"_id": new_id})
        prize = new_doc["prize"]
        item = new_doc["item"]
        usr = new_doc["winner"]
        if item:
            prize = f"{prize} {item}"
        time = int(datetime.utcnow().timestamp())
        collection.update_one({"_id": f"current_payout_{interaction.guild.id}"}, {"$set": {"user": usr, "prize": prize, "current_id": new_id, "time": time, "current": current}})
        if item:
            command = f"/serverevents payout user:{usr} quantity:{prize.split(' ')[0]} item:{item}"
        else:
            command = f"/serverevents payout user:{usr} quantity:{prize}"
        if "claimed_at" in new_doc.keys():
            claimed = f"<t:{new_doc['claimed_at']}:R>"
        else:
            claimed = "None"
        if doc["platform"] == 2:    
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Press the below buttons to execute:**\n- skip: skip this payout\n- reject: reject this payout\n- exit: exit the payout proccess\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
            embed.add_field(name="Easy Copy Version", value=f"```{command}```", inline=False)
        else:
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
        embed.set_footer(text=f"Payout {current}/{doc['amount']}")
        embed.add_field(name="Command", value=command, inline=False)
        if doc["platform"] == 1:
            content = command
        else:
            content = None
        view = ViewPayout(self.bot)
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{new_doc['link']}", emoji="🔗"))
        try:
            await self.state.last_responses[interaction.guild.id].delete()
        except:
            pass
        self.state.last_responses[interaction.guild.id] = await interaction.send(content=content, embed=embed, ephemeral=True, view=view)
        queue_msg = other_doc["queuemsg"].split("/")[6]
        queue_msg = await self.bot.get_channel(queue).fetch_message(int(queue_msg))
        embed = queue_msg.embeds[0]
        embed.title = "Payout Rejected"
        embed.color = 16711680
        embed.add_field(name="Rejected By", value=f"{interaction.user.mention}", inline=True)
        await queue_msg.edit(embed=embed, view=None)
        collec.update_one({"_id": f"payout_stats_{interaction.guild.id}"}, {"$inc": {"rejected": 1}})
        await asyncio.sleep(60)
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["time"] == time:
            await interaction.send("Inactivity detected. Exiting payout process.", ephemeral=True)
            await self.state.last_responses[interaction.guild.id].delete()
            collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})

class EventModal(nextcord.ui.Modal):
    def __init__(self, bot, interaction, list, quan, item, message_id, former_interaction):
        super().__init__(
            "Event Type",
                        timeout=300,
        )

        self.event_name = nextcord.ui.TextInput(
            label="Event Name",
            placeholder="Enter the event type (e.g. mafia, rumble, etc)",
            min_length=1,
            max_length=20,
            required=True,
        )
        self.add_item(self.event_name)
        self.bot = bot
        self.interaction = interaction
        self.list = list
        self.quan = quan
        self.item = item
        self.message_id = message_id
        self.former_interaction = former_interaction
                
    async def callback(self, modal_interaction: nextcord.Interaction):
        await modal_interaction.response.defer(ephemeral=True)
        event = self.event_name.value.lower()
        embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for {len(self.list)} winners.")
        embed.set_footer(text=f"This time may vary depending on the amount of winners.")
        await self.former_interaction.edit(embed=embed, view=None)
        for usr in self.list:
            args = [usr, self.quan, self.item, self.message_id, event]
            await self.bot.get_cog("payouts").queue_payout(args, modal_interaction)
        embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
        embed.color = 65280
        view = QueuedPayoutsView()
        config = configuration.find_one({"_id": "config"})
        claim = config[f"claim"]
        claim = claim[f"{modal_interaction.guild.id}"]
        view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{modal_interaction.guild.id}/{claim}/", emoji="🔗"))
        await self.former_interaction.edit(embed=embed, view=view)
        channel = self.bot.get_channel(modal_interaction.channel.id)
        message = await channel.fetch_message(self.message_id)
        await message.add_reaction(loading_emoji)

class payouts(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.queue_cache = {}
        self.state = PayoutState.get_instance()
        self.embed = nextcord.Embed(title="Bot Banned", description="You are banned from using this bot. Please contact the bot owner if you believe this is an error. \n\n **Reason:** Direct violation of the Terms of Service.", color=16711680)

    async def ban_check(interaction: nextcord.Interaction):
        config = configuration.find_one({"_id": "config"})
        payout = config[f"payout"]
        claim = config[f"claim"]
        queue = config[f"queue"]
        root = config[f"root"]
        guild = str(interaction.guild.id)
        if guild not in claim or guild not in queue or guild not in payout or guild not in root:
            await interaction.response.send_message(content="You have not fully configured the payout system. Please run `/config` to configure the payout system.", ephemeral=True)
            return False

        banned_users = misc.find_one({"_id": "bot_banned"})
        if banned_users:
            if str(interaction.user.id) in banned_users:
                embed = nextcord.Embed(title="Bot Banned", description=f"You are banned from using this bot. Please contact the bot owner if you believe this is an error. \n\n **Reason:** {banned_users[str(interaction.user.id)]}", color=16711680)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
            else:
                return True
        else:
            return True
        
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Payouts cog loaded.")
        self.bot.add_view(View(self.bot))
        self.bot.add_view(QueuedPayoutsView())
        self.bot.add_view(QueueView())
        self.bot.add_view(QueuedView(self.bot))
        self.check_queue.start()
        self.check_payouts.start()
        self.cache_payouts.start()

    @commands.command(name="payoutstats", aliases=["pstats"])
    async def payoutstats(self, ctx):
        doc = collec.find_one({"_id": f"payout_stats_{ctx.guild.id}"})
        embed = nextcord.Embed(title=f"Payout Stats for {ctx.guild.name}", description=f"- **Queued:** ⏣ {doc['queued']:,}\n- **Queued Amount:** {doc['queued_amt']}\n- **Claimed:** ⏣ {doc['claimed']:,}\n- **Claimed Amount:** {doc['claimed_amt']}\n- **Paid:** ⏣ {doc['paid']:,}\n- **Paid Amount:** {doc['paid_amt']}\n- **Rejected:** {doc['rejected']}")
        embed.set_footer(text="Logged since 12/17/2024", icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="payoutpurge", aliases=["purgepay"])
    async def payoutpurge(self, ctx):
        if ctx.author.id != 1166134423146729563:
            return
        docs = list(collection.find())
        for doc in docs:
            if not isinstance(doc["_id"], int):
                collection.delete_one({"_id": doc["_id"]})
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content="All false payout documents have been purged.", mention_author=False)

    @commands.command(name="rstatsreset", aliases=["rstatsr"])
    async def rstatsreset(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        if not ctx.author.guild_permissions.administrator:
            return
        collec.delete_one({"_id": "rc_root"})
        collec.insert_one({"_id": "rc_root"})
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(content="Root payout stats have been reset.", mention_author=False)

    @commands.command(name="rootstats", aliases=["rstats"])
    async def rootstats(self, ctx):
        if ctx.guild.id != RC_ID:
            return
        doc = collec.find_one({"_id": "rc_root"})
        doc.pop("_id")
        sorted_stats = sorted(doc.items(), key=lambda item: item[1], reverse=True)
        items_per_page = 10
        pages = [sorted_stats[i:i + items_per_page] for i in range(0, len(sorted_stats), items_per_page)]
        total_pages = len(pages)
        current_page = 0

        def generate_embed(page):
            descp = ""
            num = page * items_per_page + 1
            for key, value in pages[page]:
                descp += f"{num}. <@{key}> | {value} Payouts\n"
                num += 1
            embed = nextcord.Embed(
                title="Root Payout Stats",
                description=descp,
                color=nextcord.Color.yellow())
            embed.set_footer(text=f"Page {page + 1}/{total_pages} | Logged since 1/03/2024", icon_url=ctx.guild.icon.url)
            return embed

        class PaginatorView(nextcord.ui.View):
            def __init__(self):
                super().__init__()
                self.current_page = 0

            @nextcord.ui.button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.primary)
            async def previous_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                if self.current_page > 0:
                    self.current_page -= 1
                    embed = generate_embed(self.current_page)
                    await interaction.response.edit_message(embed=embed, view=self)
                self.update_buttons()

            @nextcord.ui.button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.primary)
            async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                if self.current_page < total_pages - 1:
                    self.current_page += 1
                    embed = generate_embed(self.current_page)
                    await interaction.response.edit_message(embed=embed, view=self)
                self.update_buttons()

            def update_buttons(self):
                self.children[0].disabled = self.current_page == 0
                self.children[1].disabled = self.current_page == total_pages - 1

        view = PaginatorView()
        view.update_buttons()
        embed = generate_embed(current_page)
        await ctx.reply(embed=embed, view=view, mention_author=False)
        

    @commands.command(name="howmanypayouts")
    async def howmanypayouts(self, ctx):
        docs = list(collection.find({"guild": ctx.guild.id}))
        if len(docs) == 0:
            await ctx.reply(content="No current payouts found.", mention_author=False)
            return
        payouts_count = len(docs)
        oldest_payout = docs[0]["claimed_at"]
        oldest_payout = int(oldest_payout)
        await ctx.reply(f"There are currently `{payouts_count}` payouts queued. The oldest payout was <t:{oldest_payout}:R>.", mention_author=False)

    @tasks.loop(seconds=20)
    async def cache_payouts(self):
        config = configuration.find_one({"_id": "config"})
        self.cache = config["payout"]
        self.queue_cache = config["queue"]
            
    @tasks.loop(minutes=10)
    async def check_payouts(self):
        guilds = self.bot.guilds
        config = configuration.find_one({"_id": "config"})
        root = config[f"root"]
        payout = config[f"payout"]
        for guild in guilds:
            doc = collection.find_one({"_id": f"current_payout_{guild.id}"})
            if doc is not None:
                continue
            elif str(guild.id) not in payout or str(guild.id) not in root:
                continue
            docs = list(collection.find({"guild": guild.id}))
            docs = len(docs)
            last_reminder = misc.find_one({"_id": f"payout_reminders"})
            if last_reminder:
                try:
                    last_reminder = last_reminder[f"{guild.id}"]
                except:
                    last_reminder = 0
            else:
                last_reminder = 0
            current_time = int(datetime.utcnow().timestamp())
            if docs >= 50 and current_time - last_reminder >= 14400:
                channel = self.bot.get_channel(payout[f"{guild.id}"])
                await channel.send(content=f"<@&{root[f"{guild.id}"]}> More than 50 payouts (currently {docs}) are currently in the queue. Please start the payout queue via running </payout express:1328798429081505853>.")
                misc.update_one({"_id": f"payout_reminders"}, {"$set": {f"{guild.id}": current_time}}, upsert=True)

    @tasks.loop(minutes=3)
    async def check_queue(self):
        entries = list(queuecollection.find())
        config = configuration.find_one({"_id": "config"})
        for entry in entries:
            claim = config["claim"]
            id = entry["_id"]
            guild = entry["guild"]
            id = int(id)
            try:
                claim = claim[str(guild)]
            except:
                continue
            guild = self.bot.get_guild(guild)
            try:
                msg = guild.get_channel(int(claim))
                msg = await msg.fetch_message(int(id))
            except:
                continue
            msg_creation_time = int(msg.created_at.timestamp())
            current_time = int(datetime.utcnow().timestamp())
            if (current_time - msg_creation_time) > 86400:
                embed = msg.embeds[0]
                embed.title = "Payout Expired"
                embed.color = 16711680
                view = nextcord.ui.View()
                view.add_item(nextcord.ui.Button(label="Event Message", url=f"{entry['link']}", emoji="🔗"))
                await msg.edit(embed=embed, view=view)
                queuecollection.delete_one({"_id": msg.id})
                try:
                    host = entry["host"]
                    host = await self.bot.fetch_user(host)
                    await host.send(content=f"This [payout]({msg.jump_url}) has expired because it was not claimed within 24 hours.")
                except:
                    pass
            elif (current_time - msg_creation_time) > 43200:
                if str("reminder") in entry:
                    continue
                id = entry["_id"]
                id = int(id)
                msg = guild.get_channel(claim)
                msg = await msg.fetch_message(id)
                url = msg.jump_url
                view = nextcord.ui.View()
                view.add_item(nextcord.ui.Button(label="Claim Payout", url=f"{url}", emoji="🔗"))
                embed = nextcord.Embed(title="Unclaimed Payout", description=f"This payout will expire in 12 hours if it is not claimed. Make sure to click the button below and claim your payout before it expires.", color=16711680)
                queuecollection.update_one({"_id": entry["_id"]}, {"$set": {"reminder": True}})
                try:
                    winner = entry["winner"]
                    winner = await self.bot.fetch_user(winner)
                    await winner.send(embed=embed, view=view)
                except:
                    pass

    async def get_choices(self, interaction, current: str) -> List[str]:
        prefix_query = {"_id": {"$regex": f"^{current}", "$options": "i"}}
        choices = [doc["_id"] for doc in itemcollection.find(prefix_query).limit(25)]
        if not choices:
            word_query = {"_id": {"$regex": f"\\b{current}", "$options": "i"}}
            choices = [doc["_id"] for doc in itemcollection.find(word_query).limit(25)]
            
        return choices
    
    async def get_message(self, interaction, message_id):
        msg = None
        if message_id:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://google.com") as response:
                        if response.status == 200:
                            msg = await interaction.channel.fetch_message(message_id)
                        else:
                            await interaction.send(content="Unable to find a message ID, make sure it is correct.", ephemeral=True)
                            return
            except:
                await interaction.send(content="Unable to find a message ID, make sure it is correct.", ephemeral=True)
                return
            if loading_emoji in [str(reaction.emoji) for reaction in msg.reactions if reaction.me]:
                await interaction.send(content="That message has already been used for a payout.", ephemeral=True)
                return
        else:
            try:
                messages = []
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://google.com") as response:
                        if response.status == 200:
                            messages = [msg async for msg in interaction.channel.history(limit=20)]
                        else:
                            await interaction.send(content="API connection failed. Please try using a manual message ID.", ephemeral=True)
                            return
                for message in messages:
                    if message.author.bot:
                        if loading_emoji not in [str(reaction.emoji) for reaction in message.reactions if reaction.me] and "locked" not in message.content.lower():
                            if message.author.id == self.bot.user.id and message.content == "":
                                continue
                            elif "your mafia" in message.content.lower():
                                continue
                            elif message.embeds:
                                if message.embeds[0].author:
                                    if "calculate" in message.embeds[0].author.name.lower():
                                        continue
                            msg = message
                            break
            except:
                await interaction.send(content="Unable to find a message ID, make sure it is correct.", ephemeral=True)
                return
        return msg

    @nextcord.slash_command(description="Payout commands.", name="payout")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def payout(self, interaction: nextcord.Interaction):
        pass

    @payout.subcommand(description="Queue multiple payouts at once with different prizes per winner.", name="multiple")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def payout_multiple(self, interaction: nextcord.Interaction,
                              event: str = SlashOption(description="The event to queue a payout for."),
                              winners_list: str = SlashOption(description="The list of winners that won the event with spaces separated."),
                              winner_1_quantity: str = SlashOption(description="The quantity of the first winner to pay out."),
                              winner_2_quantity: str = SlashOption(description="The quantity of the second winner to pay out."),
                              winner_3_quantity: Optional[str] = SlashOption(description="The quantity of the third winner to pay out."),
                              winner_4_quantity: Optional[str] = SlashOption(description="The quantity of the fourth winner to pay out."),
                              winner_5_quantity: Optional[str] = SlashOption(description="The quantity of the fifth winner to pay out."),
                              item: Optional[str] = SlashOption(description="The item to queue for the first winner.", autocomplete=True),
                              message_id: Optional[str] = SlashOption(description="The message id of the event.")):
        
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.send(content="You do not have permission to use this command.", ephemeral=True)
            return
        
        if message_id is None and interaction.channel.category.id == 1205547662502264882:
            await interaction.send(content="You must manually input a message ID in the giveaway channel.", ephemeral=True)
            return
        
        msg = None
        msg = await self.get_message(interaction, message_id)
            
        if msg is None:
            await interaction.send(content="Unable to find a message ID, make sure it is correct.", ephemeral=True)
            return
        
        messageid = msg.id
        winners = winners_list.split(" ")
        winners_count = len(winners)
        winner_details = []
        if winner_1_quantity:
            winner_details.append((winner_1_quantity, item))
        if winner_2_quantity:
            winner_details.append((winner_2_quantity, item))
        if winner_3_quantity:
            winner_details.append((winner_3_quantity, item))
        if winner_4_quantity:
            winner_details.append((winner_4_quantity, item))
        if winner_5_quantity:
            winner_details.append((winner_5_quantity, item))

        if winners_count != len(winner_details):
            await interaction.send(
                content=f"Number of winners ({winners_count}) does not match number of prize details provided ({len(winner_details)})", 
                ephemeral=True
            )
            return
        
        confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to proceed with payouts for {len(winner_details)} winners?", color=nextcord.Color.blue())
        confirmation_embed.add_field(name="Event", value=event, inline=True)
        for i, (winner, (quantity, item)) in enumerate(zip(winners, winner_details), 1):
            winner = winner.replace("<@", "").replace(">", "")
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = quantity.lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await interaction.send("Invalid quantity format. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return
            if item is not None:
                try:
                    itemcollection.find_one({"_id": item})["price"]
                except:
                    await interaction.send(content="Item not found in database. Please make sure to use the autocomplete options and not enter the item name manually.", ephemeral=True)
                    return
            confirmation_embed.add_field(
                name=f"Winner {i}", 
                value=f"<@{winner}>\n**Quantity:** {quantity:,}\n**Item:** {item if item else 'None'}", 
                inline=True
            )

        confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.green)
        cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.red)

        async def confirm_callback_2(interaction):  
            await interaction.response.defer()    
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for {len(winners)} winners.")
            embed.set_footer(text=f"This time may vary depending on the amount of winners.")
            await former_interaction.edit(embed=embed, view=None)
            nonlocal messageid
            num = 0
            for winner in winners:
                quan = winner_details[num][0]
                item = winner_details[num][1]
                winner = winner.replace("<@", "")
                winner = winner.replace(">", "")
                winner = int(winner)
                if quan[-1] in multipliers:
                    try:
                        numeric_part = float(quan[:-1])
                        multiplier = multipliers[quan[-1]]
                        quan = int(numeric_part * multiplier)
                    except ValueError:
                        await interaction.response.send_message(content="Invalid quantity format. Please use a number followed by k, m, b, or t.", ephemeral=True)
                        return
                else:
                    if ',' in quan:
                        quan = quan.replace(',', '')
                    try:
                        quan = int(quan)
                    except ValueError:
                        await interaction.response.send_message(content="Invalid quantity. Please enter a number.", ephemeral=True)
                        return
                args = [winner, quan, item, messageid, event]
                await self.queue_payout(args, interaction)
                num += 1
            embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
            embed.color = 65280
            view = QueuedPayoutsView()
            config = configuration.find_one({"_id": "config"})
            claim = config[f"claim"]
            claim = claim[f"{interaction.guild.id}"]
            view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{interaction.guild.id}/{claim}/", emoji="🔗"))
            await former_interaction.edit(embed=embed, view=view)
            try:
                msg = await interaction.channel.fetch_message(message_id)
                await msg.add_reaction("<a:loading_animation:1218134049780928584>")
            except:
                pass
            

        async def cancel_callback_2(interaction):
            await interaction.response.defer()
            await former_interaction.edit(content="Payouts have been canceled.", embed=None, view=None)

        confirm_button.callback = confirm_callback_2
        cancel_button.callback = cancel_callback_2

        view = nextcord.ui.View()
        view.add_item(confirm_button)
        view.add_item(cancel_button)

        msg = await interaction.send(embed=confirmation_embed, view=view, ephemeral=True)
        former_interaction = msg
        await asyncio.sleep(10)
        try:
            await interaction.delete_original_message()
        except:
            return
        
    async def auction_payout(self, args, interaction):
        config = configuration.find_one({"_id": "config"})
        queue = config[f"queue"]
        claim = config[f"claim"]
        root = config[f"root"]
        payout = config[f"payout"]
        guild_id = str(interaction.guild.id)
        if guild_id not in queue or guild_id not in claim or guild_id not in root or guild_id not in payout:
            await interaction.send(content="You have not fully configured the payout system. Please run `/config` to configure the payout system.", ephemeral=True)
            return
        queue = queue[f"{interaction.guild.id}"]
        usr = self.bot.get_user(args[0])
        quan = args[1]
        item = args[2]
        message_id = args[3]
        event = args[4]
        channel = self.bot.get_channel(queue)
        msg_channel = self.bot.get_channel(interaction.channel.id)
        msg = await msg_channel.fetch_message(message_id)
        embed = nextcord.Embed(title="Payout Queued", color=000000)
        embed.set_footer(text=f"Queued by Compass#1919")
        embed.timestamp = datetime.utcnow()
        embed.add_field(name="Information", value=f"{DOT} **Winner:** {usr.mention}\n{DOT} **Event:** {event}", inline=True)
        if item:
            value = itemcollection.find_one({"_id": item})
            try:
                value = value["price"]
            except:
                await interaction.send(content="Item not found in database. Please queue manually.", ephemeral=True)
                return
            value = int(value)
            value = value * quan
            embed.add_field(name="Prize Info", value=f"{DOT} **Won:** `{quan}x` {item}\n{DOT} **Value:** ⏣ {value:,}", inline=True)
        else:
            value = int(quan)
            embed.add_field(name="Prize Info", value=f"{DOT} **Won:** `⏣  {quan:,}`", inline=True)
        view = QueueView()
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{msg.jump_url}", emoji="🔗"))
        response = await channel.send(embed=embed, view=view)
        doc = {
            "_id": response.id,
            "host": interaction.user.id,
            "winner": usr.id,
            "link": msg.jump_url,
            "prize": quan,
            "item": item,
            "value": value,
            "event": event,
            "claimed_at": int(datetime.utcnow().timestamp()),
            "queuemsg": response.jump_url,
            "guild": interaction.guild.id
        }
        collection.insert_one(doc)
        collec.update_one({"_id": f"payout_stats_{interaction.guild.id}"}, {"$inc": {"queued": value, "queued_amt": 1, "claimed": value, "claimed_amt": 1}})

    async def calculator(self, interaction, quantity):
        numbers = re.split(r'[+\-*/^%]', quantity)
        for number in numbers:
            if "k" in number:
                old_number = number.replace("k", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000
                quantity = quantity.replace(number, str(old_number))
            elif "m" in number:
                old_number = number.replace("m", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000
                quantity = quantity.replace(number, str(old_number))
            elif "b" in number:
                old_number = number.replace("b", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000000
                quantity = quantity.replace(number, str(old_number))
            elif "t" in number:
                old_number = number.replace("t", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000000000
                quantity = quantity.replace(number, str(old_number))
        try:
            quantity = eval(quantity)
            quantity = float(quantity) // 1
            quantity = int(quantity)
        except:
            return
        return str(quantity)
        
    @payout.subcommand(description="Queue a payout.", name="create")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def payout_queue(self, interaction: nextcord.Interaction,
                           winners_list: str = SlashOption(description="The list of winners that won the event with spaces separated."),
                           quantity: str = SlashOption(description="The quantity of each winner to pay out."),
                           item: Optional[str] = SlashOption(description="The item to payout", autocomplete=True),
                           message_id: Optional[str] = SlashOption(description="The message id of the event."),
                           override: Optional[bool] = SlashOption(description="Allow using message IDs that have been used for a payout.", default=False),
                           event: Optional[str] = SlashOption(description="The event to queue a payout for.")):
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            return
        config = configuration.find_one({"_id": "config"})
        event_manager = config[f"event_manager_role"]
        if str(interaction.guild.id) in event_manager:
            event_manager = event_manager[f"{interaction.guild.id}"]
        else:
            event_manager = 1
        roles = [role.id for role in interaction.user.roles]
        if not interaction.user.guild_permissions.manage_messages and event_manager not in roles:
            await interaction.send(content="You do not have permission to use this command.", ephemeral=True)
            return
        if message_id is None and interaction.channel.category.id == 1205547662502264882:
            await interaction.send(content="You must manually input a message ID in the giveaway channel.", ephemeral=True)
            return
        if override is None:
            override = False
        msg = None
        msg = await self.get_message(interaction, message_id)


        if not msg:
            await interaction.send(content="No valid message found. Please enter manually.", ephemeral=True)
            return
        
        msgid = msg.id
        
        if event is not None:
            event = event.lower()
        
        if item:
            try:
                itemcollection.find_one({"_id": item})["price"]
            except:
                await interaction.send(content="Item not found in database. Please make sure to use the autocomplete options and not enter the item name manually.", ephemeral=True)
                return
        
        if not event:
            if msg.author.id in DICT.keys():
                event = DICT[msg.author.id]
            elif interaction.channel.id == 1240782193270460476:
                event = "auction"
            else:
                event = "Enter after confirmation."

        quantity = quantity.lower()
        args = ["+", "-", "*", "/"]
        if any(arg in quantity for arg in args):
            quantity = await self.calculator(interaction, quantity)
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(quantity[:-1])
                multiplier = multipliers[quantity[-1]]
                quantity = int(numeric_part * multiplier)
            except ValueError:
                await interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                return
        else:
            if ',' in quantity:
                quantity = quantity.replace(',', '')
            try:
                quantity = int(quantity)
            except ValueError:
                await interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                return
        quan = quantity
        winners = winners_list.split(" ")
        list = []
        for winner in winners:
            winner = winner.replace("<@", "")
            winner = winner.replace(">", "")
            try:
                list.append(int(winner))
            except:
                await interaction.send(content="Invalid winner. Please enter a valid user ID.", ephemeral=True)
                return
        if quan <= 0:
            await interaction.send(content="You have entered an invalid quantity. Please enter a number greater than 0.", ephemeral=True)
            return
        winners = ", ".join([f"<@{usr}>" for usr in list])
        confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to proceed with payouts for {len(list)} winners?\n\n{DOT} **Event:** {event}\n{DOT} **Winners:** {winners}\n{DOT} **Quantity:** {quan:,}\n{DOT} **Item:** {item if item else 'None'}\n{DOT} **Message:** {msg.jump_url}", color=nextcord.Color.blue())
        confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.green)
        cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.red)

        was_confirmed = False
        view = nextcord.ui.View()
        view.add_item(confirm_button)
        view.add_item(cancel_button)
        msg = await interaction.send(embed=confirmation_embed, view=view, ephemeral=True)
        former_interaction = msg

        async def confirm_callback(interaction):
            nonlocal was_confirmed
            nonlocal msgid
            was_confirmed = True
            if event == "Enter after confirmation.":
                modal = EventModal(self.bot, interaction, list, quan, item, msgid, former_interaction)
                await interaction.response.send_modal(modal)
                await asyncio.sleep(10)
                try:
                    await interaction.response.defer(ephemeral=True)
                    await former_interaction.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)
                except:
                    return
                return
            await interaction.response.defer()        
            embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for {len(list)} winners.")
            embed.set_footer(text=f"This time may vary depending on the amount of winners.")
            await former_interaction.edit(embed=embed, view=None)
            for usr in list:
                args = [usr, quan, item, msgid, event]
                await self.queue_payout(args, interaction)
            embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
            embed.color = 65280
            view = QueuedPayoutsView()
            config = configuration.find_one({"_id": "config"})
            claim = config[f"claim"]
            claim = claim[f"{interaction.guild.id}"]
            view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{interaction.guild.id}/{claim}/", emoji="🔗"))
            await former_interaction.edit(embed=embed, view=view)
            channel = self.bot.get_channel(interaction.channel.id)
            message = await channel.fetch_message(int(msgid))
            await message.add_reaction(loading_emoji)
            await asyncio.sleep(5)
            try:
                await former_interaction.delete()
            except:
                return

        async def cancel_callback(interaction):
            nonlocal was_confirmed
            was_confirmed = True
            await interaction.response.defer()
            await former_interaction.edit(content="Payouts have been canceled.", embed=None, view=None)
            await asyncio.sleep(3)
            try:
                await former_interaction.delete()
            except:
                return
        confirm_button.callback = confirm_callback
        cancel_button.callback = cancel_callback
        await asyncio.sleep(10)
        if not was_confirmed:
            await msg.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)
    
    async def queue_payout(self, args, interaction):
        try:
            usr = self.bot.get_user(args[0])
        except:
            await interaction.send("Fetching user failed. Please try again.", ephemeral=True)
            return
        if not usr:
            try:
                await interaction.send("User not found. Please try again.", ephemeral=True)
            except:
                await interaction.user.send("User not found. Please try again.")
                return
        quan = args[1]
        item = args[2]
        message_id = args[3]
        event = args[4]
        config = configuration.find_one({"_id": "config"})
        claim = config[f"claim"]
        queue = config[f"queue"]
        root = config[f"root"]
        payout = config[f"payout"]
        guild_id = str(interaction.guild.id)
        if guild_id not in queue or guild_id not in claim or guild_id not in root or guild_id not in payout:
            await interaction.send(content="You have not fully configured the payout system. Please run `/config` to configure the payout system.", ephemeral=True)
            return
        claim = claim[f"{interaction.guild.id}"]
        queue = queue[f"{interaction.guild.id}"]
        if item is None:
            value = f"⏣ {quan:,}"
            item = False
            item_value = quan
        else:
            value = f"`{quan}x` {item}"
            try:
                item_value = itemcollection.find_one({"_id": item})["price"]
            except:
                item_value = 0
            item_value = int(item_value) * quan
        
        embed = nextcord.Embed(title=f"Payout Queued")
        try:
            embed.set_footer(text=f"Queued by {interaction.user.name}")
        except:
            embed.set_footer(text=f"Queued by {interaction.author.name}")
        embed.timestamp = datetime.now()
        embed.add_field(name="Information", value=f"{DOT} **Winner:** {usr.mention}\n{DOT} **Event:** {event}", inline=True)
        if not item:
            embed.add_field(name="Prize Info", value=f"{DOT} **Won:** `{value}`", inline=True)
        else:
            embed.add_field(name="Prize Info", value=f"{DOT} **Won:** {value}\n{DOT} **Value:** `{item_value:,}`", inline=True)
        content = f"{usr.mention} your winnings have been queued. \n> Please claim it <t:{int(time.time() + 86400)}:R> or you will forfeit your winnings."
        view = View(self.bot)
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message_id}", emoji="🔗"))
        response = await self.bot.get_channel(claim).send(content=content, embed=embed, view=view)
        try:
            queuecollection.insert_one({"_id": response.id, "host": interaction.user.id, "winner": usr.id, "event": event, "prize": quan, "link": f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message_id}", "item": item, "value": item_value, "guild": interaction.guild.id})
        except:
            queuecollection.insert_one({"_id": response.id, "host": interaction.author.id, "winner": usr.id, "event": event, "prize": quan, "link": f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{message_id}", "item": item, "value": item_value, "guild": interaction.guild.id})
        collec.update_one({"_id": f"payout_stats_{interaction.guild.id}"}, {"$inc": {"queued": item_value, "queued_amt": 1}})
            
    
    @payout.subcommand(description="Start paying the payouts.", name="express")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def payouts(self, interaction,
                      platform: Optional[int] = SlashOption(name="platform", description="The platform to pay out on.", required=False, choices={"Mobile": 1, "PC": 2})):
        user_roles = [role.id for role in interaction.user.roles]
        config = configuration.find_one({"_id": "config"})
        root = config[f"root"]
        root = root[f"{interaction.guild.id}"]
        payout = config[f"payout"]
        payout = payout[f"{interaction.guild.id}"]

        if root not in user_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return

        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is not None:
            time = doc["time"]
            embed = nextcord.Embed(title="Error Occured", description="There is already a payout process currently running. Please wait for it to finish before starting a new one, or click the button below to override the current payout process.", color=000000)
            view = OverrideView()
            current_time = int(datetime.utcnow().timestamp())
            if current_time - time > 600:
                await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
                return
            else:
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
        elif interaction.channel.id != payout:
            await interaction.response.send_message(f"This command must be used in the <#{payout}> channel.", ephemeral=True)
            return
        
        docs = collection.find({"guild": interaction.guild.id}).sort("claimed_at", 1)
        payout_ids = []
        for doc in docs:
            payout_ids.append(doc["_id"])
        
        if len(payout_ids) == 0:
            await interaction.response.send_message("There are no payouts in the queue.", ephemeral=True)
            return
        
        if not platform:
            platform = 1
        
        doc = collection.find_one({"_id": payout_ids[0]})
        prize = doc["prize"]
        item = doc["item"]
        if item:
            prize = f"{prize} {item}"
        time = int(datetime.utcnow().timestamp())
        collection.insert_one({
            "_id": f"current_payout_{interaction.guild.id}",
            "payouter": interaction.user.id,
            "payout_slice": payout_ids,
            "user": doc["winner"],
            "platform": platform,
            "prize": prize,
            "current_id": payout_ids[0],
            "time": time,
            "amount": len(payout_ids),
            "current": 1
        })
        if "claimed_at" in doc.keys():
            claimed = f"<t:{doc['claimed_at']}:R>"
        else:
            claimed = "None"
        if item:
            command = f"/serverevents payout user:{doc['winner']} quantity:{prize.split(' ')[0]} item:{item}"
        else:
            command = f"/serverevents payout user:{doc['winner']} quantity:{prize}"
        await interaction.response.send_message(f"# Starting payout process with {len(payout_ids)} payouts in queue from {claimed}", ephemeral=True)
        await asyncio.sleep(1)
        channel = doc["link"].split("/")[5]
        usr = doc["winner"]
        guild_name = interaction.guild.name
        if platform == 2:
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {doc['value']:,}\n**Channel:** <#{channel}>\n**Host:** <@{doc['host']}>\n\n**Press the below buttons to execute:**\n- skip: skip this payout\n- reject: reject this payout\n- exit: exit the payout proccess\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
            embed.add_field(name="Easy Copy Version", value=f"```{command}```", inline=False)
        else:
            embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{usr}>\n**Prize:** {prize}\n**Value:** ⏣ {doc['value']:,}\n**Channel:** <#{channel}>\n**Host:** <@{doc['host']}>\n\n**Claimed at:** {claimed}\n**Timeout:** <t:{time + 60}:R>", color=000000)
        embed.add_field(name="Command", value=command, inline=False)
        embed.set_footer(text=f"Payout 1/{len(payout_ids)}")
        if platform == 1:
            content = command
        else:
            content = None
        view = ViewPayout(self.bot)
        view.add_item(nextcord.ui.Button(label="Event Message", url=f"{doc['link']}", emoji="🔗"))
        self.state.last_interactions[interaction.guild.id] = interaction
        self.state.last_responses[interaction.guild.id] = await interaction.send(content=content, embed=embed, ephemeral=True, view=view)
        await asyncio.sleep(60)
        doc = collection.find_one({"_id": f"current_payout_{interaction.guild.id}"})
        if doc is None:
            return
        if doc["time"] == time:
            await interaction.send("Inactivity detected. Exiting payout process.", ephemeral=True)
            try:
                await self.state.last_responses[interaction.guild.id].delete()
            except:
                pass
            collection.delete_one({"_id": f"current_payout_{interaction.guild.id}"})

    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            payout = self.cache.get(str(message.guild.id))
            if not payout or message.channel.id != payout or message.author.id != 270904126974590976:
                return
            
            if not message.embeds or not message.embeds[0].description or "successfully paid" not in message.embeds[0].description.lower():
                return
            
            doc = collection.find_one({"_id": f"current_payout_{message.guild.id}"})
            if not doc:
                return
            try:
                ref_msg = message.reference.cached_message
            except:
                ref_msg = None
            if ref_msg:
                if doc["payouter"] != ref_msg.interaction.user.id:
                    return
            payouter = doc["payouter"]
            current_user, current_prize, current_id = doc["user"], str(doc["prize"]), doc["current_id"]
            other_doc = collection.find_one({"_id": current_id})
            payout_slice = doc["payout_slice"]
            content = message.embeds[0].description
            user = content.split("<@")[1].split(">")[0]

            prize = content.split("**")[1].replace("⏣ ", "").replace(",", "").split("**")[0].replace("*", "")
            if ">" in prize:
                prize = f"{prize.split(' <')[0]} {prize.split('> ')[1]}"
            
            if str(user) != str(current_user) or str(prize) != str(current_prize):
                return

            payout_slice.remove(current_id)
            queue = self.queue_cache[str(message.guild.id)]

            if not queue:
                config = configuration.find_one({"_id": "config"})
                queue = config["queue"][str(message.guild.id)]
                if not queue:
                    return
                self.queue_cache[str(message.guild.id)] = queue

            if len(payout_slice) == 0:
                await self._complete_payout(message, other_doc, queue, current_id, payouter)
                return

            new_payout = payout_slice[0]
            new_doc = collection.find_one({"_id": new_payout})
            prize = f"{new_doc['prize']} {new_doc['item']}" if new_doc["item"] else new_doc["prize"]
            time = int(datetime.utcnow().timestamp())
            current = doc["current"] + 1
            command = f"/serverevents payout user:{new_doc['winner']} quantity:{prize.split(' ')[0]} item:{new_doc['item']}" if new_doc["item"] else f"/serverevents payout user:{new_doc['winner']} quantity:{prize}"
            platform = doc["platform"]
            guild_name = message.guild.name
            embed = None
            collection.update_one({"_id": f"current_payout_{message.guild.id}"}, {"$set": {"user": new_doc["winner"], "prize": prize, "current_id": new_payout, "time": time, "payout_slice": payout_slice, "current": current}})
            if platform == 2:
                embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{new_doc['winner']}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Press the below buttons to execute:**\n- skip: skip this payout\n- reject: reject this payout\n- exit: exit the payout proccess\n\n**Claimed at:** <t:{new_doc.get('claimed_at', 'None')}:R>\n**Timeout:** <t:{time + 60}:R>", color=000000)
                embed.add_field(name="Easy Copy Version", value=f"```{command}```", inline=False)
            else:
                embed = nextcord.Embed(title=f"{guild_name} Payouts", description=f"**Winner:** <@{new_doc['winner']}>\n**Prize:** {prize}\n**Value:** ⏣ {new_doc['value']:,}\n**Channel:** <#{new_doc['link'].split('/')[5]}>\n**Host:** <@{new_doc['host']}>\n\n**Claimed at:** <t:{new_doc.get('claimed_at', 'None')}:R>\n**Timeout:** <t:{time + 60}:R>", color=000000)
            embed.add_field(name="Command", value=command, inline=False)
            embed.set_footer(text=f"Payout {current}/{doc['amount']}")
            view = ViewPayout(self.bot)
            view.add_item(nextcord.ui.Button(label="Event Message", url=f"{new_doc['link']}", emoji="🔗"))
            response = await self.state.last_interactions[message.guild.id].send(content=command if doc["platform"] == 1 else None, embed=embed, ephemeral=True, view=view)
            try:
                last = self.state.last_responses.get(message.guild.id)
                self.state.last_responses[message.guild.id] = response
            except:
                pass
            try:
                collection.delete_one({"_id": current_id})
            except:
                pass
            try:
                asyncio.create_task(self._update_queue_message(queue, other_doc, message.jump_url, new_doc, payouter))
            except Exception as e:
                print(e)
                pass
            try:
                await last.delete()
                await message.add_reaction(GREEN_CHECK)
            except:
                pass
            try:
                collec.update_one({"_id": f"payout_stats_{message.guild.id}"}, {"$inc": {"paid": other_doc["value"], "paid_amt": 1}})
            except:
                pass
            try:
                asyncio.create_task(self.check_timeout(message, time))
            except:
                pass
        except:
            return
        
    async def check_timeout(self, message, time):
        await asyncio.sleep(60)
        doc = collection.find_one({"_id": f"current_payout_{message.guild.id}"})
        if doc is None:
            return
        if doc["time"] == time:
            interaction = self.state.last_interactions.get(message.guild.id)
            last = self.state.last_responses.get(message.guild.id)
            await last.delete()
            if interaction:
                await interaction.send("Inactivity detected. Exiting payout process.", ephemeral=True)
            collection.delete_one({"_id": f"current_payout_{message.guild.id}"})
            return
        
    async def _complete_payout(self, message, other_doc, queue, current_id, payouter):
        try:
            await self.state.last_responses.get(message.guild.id).delete()
        except Exception:
            pass
        await message.add_reaction(GREEN_CHECK)
        await self.state.last_interactions.get(message.guild.id).send("All payouts have been completed.", ephemeral=True)
        
        try:
            queue_msg_id = other_doc["queuemsg"].split("/")[6]
            queue_msg = await self.bot.get_channel(queue).fetch_message(int(queue_msg_id))
            embed = queue_msg.embeds[0]
            embed.title = "Payout Paid"
            embed.color = 3066993
            view = PayoutView()
            view.add_item(nextcord.ui.Button(label="Paid At", url=message.jump_url, emoji="🔗"))
            view.add_item(nextcord.ui.Button(label="Event Message", url=other_doc["link"], emoji="🔗"))
            await queue_msg.edit(embed=embed, view=view)
        except:
            pass
        
        try:
            event_msg_channel = other_doc["link"].split("/")[5]
            event_msg_id = other_doc["link"].split("/")[6]
        except:
            pass
            
        try:
            event_msg = await self.bot.get_channel(int(event_msg_channel)).fetch_message(int(event_msg_id))
            await event_msg.clear_reactions()
            await event_msg.add_reaction(PAID)
        except Exception:
            pass
        collection.delete_one({"_id": f"current_payout_{message.guild.id}"})
        collection.delete_one({"_id": current_id})
        collec.update_one({"_id": f"payout_stats_{message.guild.id}"}, {"$inc": {"paid": other_doc["value"], "paid_amt": 1}})
        if queue == 1205270487643459617:
            collec.update_one({"_id": f"rc_root"}, {"$inc": {f"{payouter}": 1}}, upsert=True)

    async def _update_queue_message(self, queue, other_doc, jump_url, new_doc, payouter):
        try:
            if queue == 1205270487643459617:
                collec.update_one({"_id": f"rc_root"}, {"$inc": {f"{payouter}": 1}}, upsert=True)
        except:
            pass
        try:
            queue_msg = await self.bot.get_channel(queue).fetch_message(int(other_doc["queuemsg"].split("/")[6]))
            embed = queue_msg.embeds[0]
            embed.title = "Payout Paid"
            embed.color = 3066993
            view = PayoutView()
            view.add_item(nextcord.ui.Button(label="Paid At", url=jump_url, emoji="🔗"))
            view.add_item(nextcord.ui.Button(label="Event Message", url=f"{new_doc['link']}", emoji="🔗"))
            await queue_msg.edit(embed=embed, view=view)
        except Exception as e:
            print(e)
            pass
        await self._clear_event_reactions(new_doc)

    async def _clear_event_reactions(self, doc):
        try:
            event_msg_link = doc["link"]
            docs = list(collection.find({"link": event_msg_link}))
            if len(docs) > 0:
                return
            event_msg = await self.bot.get_channel(int(doc["link"].split("/")[5])).fetch_message(int(doc["link"].split("/")[6]))
            await event_msg.clear_reactions()
            await event_msg.add_reaction(PAID)
        except:
            return
            

    @payout_queue.on_autocomplete("item")
    @payout_multiple.on_autocomplete("item")
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
    bot.add_cog(payouts(bot))

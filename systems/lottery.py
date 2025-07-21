import random
import nextcord
import asyncio
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection
from typing import Dict, List, Any
from datetime import datetime, timedelta

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Lottery"]
lottery_channel = 1335329445564776458
lottery_entry = 1396702361090785290
lottery_logs = 1396702386973704374

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

class PrecisionExtractor:
    def extract_content(self, raw_json: Dict[str, Any]) -> List[str]:
        results = []
        
        def scan_component(component: Dict[str, Any]):
            for field in ['label', 'content', 'value', 'placeholder']:
                if field in component and isinstance(component[field], str):
                    text = component[field].strip()
                    if text and len(text) > 1:  
                        results.append(text)
            
            if 'components' in component:
                for child in component['components']:
                    scan_component(child)

        if 'content' in raw_json and raw_json['content']:
            results.append(raw_json['content'].strip())
        
        if 'components' in raw_json:
            for component in raw_json['components']:
                scan_component(component)

        return results

class Lottery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.extractor = PrecisionExtractor()

    @tasks.loop(hours=1)
    async def check_lottery(self):
        doc = collection.find_one({"_id": "lottery"})
        if doc:
            if doc["status"] == "active":
                total_entries = sum(doc["entries"].values())
                guild = self.bot.get_guild(1205270486230110330)
                embed = nextcord.Embed(
                    title="Robbing Central Lottery",
                    description=f"**Current Prize Pool** | `⏣ {doc['pool']:,}`\n**Entry Cost** | `⏣ {doc['entry']:,}`\n**Total Entries** | `{total_entries:,}`\n**Status** | Ends <t:{int(doc['end_time'].timestamp())}:R>",
                    color=nextcord.Color.blurple()
                )
                embed.set_footer(text=f"Robbing Central Lotteries", icon_url=guild.icon.url)
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6851/6851332.png")
                channel = guild.get_channel(lottery_channel)
                message = await channel.fetch_message(doc["message_id"])
                await message.edit(embed=embed)
                embed.title = "Robbing Central Lottery Updated"
                log_channel = guild.get_channel(lottery_logs)
                await log_channel.send(embed=embed)
            if doc["end_time"] - datetime.now() <= timedelta(hours=1):
                asyncio.create_task(self.end_lottery(doc, True))
            
    @commands.Cog.listener()
    async def on_ready(self):
        print("Lottery cog loaded.")
        self.check_lottery.start()

    async def extract(self, message):
        target = message
        route = nextcord.http.Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=target.channel.id, message_id=target.id
        )
        raw_json = await self.bot.http.request(route)
        content_pieces = self.extractor.extract_content(raw_json)
        return content_pieces

    @nextcord.slash_command(name="lottery", guild_ids=[1205270486230110330])
    async def lottery(self, interaction: nextcord.Interaction):
        pass
    
    async def end_lottery(self, doc, bool):
        if bool:
            seconds_till_end = (doc["end_time"] - datetime.now()).total_seconds()
            await asyncio.sleep(seconds_till_end)
        collection.update_one({"_id": "lottery"}, {"$set": {"status": "ended"}})
        guild = self.bot.get_guild(1205270486230110330)
        channel = guild.get_channel(lottery_channel)
        message = await channel.fetch_message(doc["message_id"])
        doc = collection.find_one({"_id": "lottery"})
        total_entries = sum(doc["entries"].values())
        entries = []
        for entrant, entry in doc["entries"].items():
            entries.extend([entrant] * entry)
        if len(entries) == 0:
            embed = nextcord.Embed(title="Lottery Ended", description="No entries were made, the lottery has been cancelled.", color=nextcord.Color.red())
            embed.set_footer(text=f"Robbing Central Lotteries", icon_url=guild.icon.url)
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6851/6851332.png")
            await message.edit(embed=embed, view=None)
            collection.delete_one({"_id": "lottery"})
            log_channel = guild.get_channel(lottery_logs)
            await log_channel.send(embed=embed)
            return
        winner = random.choice(entries)
        embed = nextcord.Embed(title="Lottery Ended", description=f"**Winner** | <@{winner}>\n**Prize Pool** | `⏣ {doc['pool']:,}`\n**Entry Cost** | `⏣ {doc['entry']:,}`\n**Total Entries** | `{total_entries}`\n**Status** | `Ended`", color=nextcord.Color.green())
        embed.set_footer(text=f"Robbing Central Lotteries", icon_url=guild.icon.url)
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6851/6851332.png")
        await message.edit(embed=embed, view=None)
        await message.reply(f"<@{winner}> you have won the lottery! Your prize will be queued in <#1205270487643459616> momentarily.")
        log_channel = guild.get_channel(lottery_logs)
        await log_channel.send(embed=embed)
        collection.delete_one({"_id": "lottery"})
        await self.bot.get_cog("payouts").queue_payout([int(winner), doc["pool"], None, message.id, "Lottery Payout"], message)
    
    async def cancel_lottery(self, doc):
        guild = self.bot.get_guild(1205270486230110330)
        channel = guild.get_channel(lottery_channel)
        message = await channel.fetch_message(doc["message_id"])
        total_entries = sum(doc["entries"].values())
        embed = nextcord.Embed(title="Lottery Cancelled", description=f"**Prize Pool** | `⏣ {doc['pool']:,}`\n**Entry Cost** | `⏣ {doc['entry']:,}`\n**Total Entries** | `{total_entries}`\n**Status** | `Ended`", color=nextcord.Color.red())
        embed.set_footer(text=f"Robbing Central Lotteries", icon_url=guild.icon.url)
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6851/6851332.png")
        await message.edit(embed=embed, view=None)
        log_channel = guild.get_channel(lottery_logs)
        await log_channel.send(embed=embed)
        entry_cost = doc["entry"]
        for user, entries in doc["entries"].items():
            try:
                amount = entry_cost * entries
                await self.bot.get_cog("payouts").queue_payout([int(user), amount, None, message.id, "Lottery Refund"], message)
            except Exception as e:
                print(e)
        collection.delete_one({"_id": "lottery"})

    @lottery.subcommand(name="end", description="Ends the current lottery and selects a winner.")
    async def end(self, interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        await self.end_lottery(doc, False)
        await interaction.response.send_message("Lottery ended successfully.", ephemeral=True)

    @lottery.subcommand(name="cancel", description="Cancels the current lottery and refunds all entries.")
    async def cancel(self, interaction: nextcord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        await self.cancel_lottery(doc)
        await interaction.response.send_message("Lottery cancelled successfully.", ephemeral=True)

    @lottery.subcommand(name="setpool", description="Sets the current lottery's pool.")
    async def setpool(self, interaction: nextcord.Interaction, amount: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        def parse_quantity(quantity_str):
            quantity = quantity_str.lower().replace(',', '').strip()
            if quantity and quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    return int(numeric_part * multiplier)
                except ValueError:
                    return None
            else:
                try:
                    return int(quantity)
                except ValueError:
                    return None
        amount = parse_quantity(amount)
        if amount is None or amount <= 0:
            await interaction.response.send_message("Invalid amount. Please use a number (optionally with k, m, b, or t).", ephemeral=True)
            return
        collection.update_one({"_id": "lottery"}, {"$set": {"pool": amount}})
        await interaction.response.send_message(f"Set the lottery pool to {amount:,}.", ephemeral=True)

    @lottery.subcommand(name="addpool", description="Adds to the current lottery's pool.")
    async def addpool(self, interaction: nextcord.Interaction, amount: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        def parse_quantity(quantity_str):
            quantity = quantity_str.lower().replace(',', '').strip()
            if quantity and quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    return int(numeric_part * multiplier)
                except ValueError:
                    return None
            else:
                try:
                    return int(quantity)
                except ValueError:
                    return None
        amount = parse_quantity(amount)
        if amount is None or amount <= 0:
            await interaction.response.send_message("Invalid amount. Please use a number (optionally with k, m, b, or t).", ephemeral=True)
            return
        collection.update_one({"_id": "lottery"}, {"$inc": {"pool": amount}})
        await interaction.response.send_message(f"Added {amount:,} to the lottery pool.", ephemeral=True)

    @lottery.subcommand(name="removepool", description="Removes from the current lottery's pool.")
    async def removepool(self, interaction: nextcord.Interaction, amount: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        def parse_quantity(quantity_str):
            quantity = quantity_str.lower().replace(',', '').strip()
            if quantity and quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    return int(numeric_part * multiplier)
                except ValueError:
                    return None
            else:
                try:
                    return int(quantity)
                except ValueError:
                    return None
        amount = parse_quantity(amount)
        if amount is None or amount <= 0:
            await interaction.response.send_message("Invalid amount. Please use a number (optionally with k, m, b, or t).", ephemeral=True)
            return
        collection.update_one({"_id": "lottery"}, {"$inc": {"pool": -amount}})
        await interaction.response.send_message(f"Removed {amount:,} from the lottery pool.", ephemeral=True)

    @lottery.subcommand(name="addentries", description="Adds entries to a user for the current lottery.")
    async def addentries(self, interaction: nextcord.Interaction, user: nextcord.Member, quantity: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        if user.id not in doc["entries"]:
            doc["entries"][str(user.id)] = 0
        doc["entries"][str(user.id)] += quantity
        collection.update_one({"_id": "lottery"}, {"$set": {"entries": doc["entries"]}})
        await interaction.response.send_message(f"Added {quantity} entries to {user.mention}.", ephemeral=True)

    @lottery.subcommand(name="removeentries", description="Removes entries from a user for the current lottery.")
    async def removeentries(self, interaction: nextcord.Interaction, user: nextcord.Member, quantity: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if not doc:
            await interaction.response.send_message("There is no ongoing lottery.", ephemeral=True)
            return
        if user.id not in doc["entries"]:
            doc["entries"][str(user.id)] = 0
        doc["entries"][str(user.id)] -= quantity
        collection.update_one({"_id": "lottery"}, {"$set": {"entries": doc["entries"]}})
        await interaction.response.send_message(f"Removed {quantity} entries from {user.mention}.", ephemeral=True)

    @lottery.subcommand(name="create", description="Creates a new lottery.")
    async def create(self, interaction: nextcord.Interaction, entry_cost: str, days: str, initial_pool: str):
        if interaction.channel.id != lottery_channel:
            await interaction.response.send_message("This command can only be used in the lottery channel.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        doc = collection.find_one({"_id": "lottery"})
        if doc:
            await interaction.response.send_message("There is already an ongoing lottery.", ephemeral=True)
            return
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}

        def parse_quantity(quantity_str):
            quantity = quantity_str.lower().replace(',', '').strip()
            if quantity and quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    return int(numeric_part * multiplier)
                except ValueError:
                    return None
            else:
                try:
                    return int(quantity)
                except ValueError:
                    return None

        entry_cost_val = parse_quantity(entry_cost)
        if entry_cost_val is None or entry_cost_val <= 0:
            await interaction.response.send_message("Invalid entry cost. Please use a number (optionally with k, m, b, or t).", ephemeral=True)
            return

        initial_pool_val = parse_quantity(initial_pool)
        if initial_pool_val is None or initial_pool_val < 0:
            await interaction.response.send_message("Invalid initial pool. Please use a number (optionally with k, m, b, or t).", ephemeral=True)
            return

        try:
            days_val = float(days)
            if days_val <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("Invalid number of days. Please enter a positive number.", ephemeral=True)
            return
        end_time = datetime.now() + timedelta(days=days_val)
        collection.insert_one({"_id": "lottery", "pool": initial_pool_val, "entries": {}, "start_time": datetime.now(), "entry": entry_cost_val, "days": days_val, "end_time": end_time, "host": interaction.user.id, "status": "active", "message_id": None})
        embed = nextcord.Embed(
            title="Robbing Central Lottery",
            description=f"**Current Prize Pool** | `⏣ {initial_pool_val:,}`\n**Entry Cost** | `⏣ {entry_cost_val:,}`\n**Total Entries** | `0`\n**Status** | Ends <t:{int(end_time.timestamp())}:R>",
            color=nextcord.Color.blurple()
        )
        embed.set_footer(text=f"Robbing Central Lotteries", icon_url=interaction.guild.icon.url)
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/6851/6851332.png")
        view = nextcord.ui.View()
        view.add_item(nextcord.ui.Button(label="🎰 Enter Lottery", style=nextcord.ButtonStyle.green, url=f"https://discord.com/channels/{interaction.guild.id}/{lottery_entry}"))
        message = await interaction.channel.send(embed=embed, view=view)
        collection.update_one({"_id": "lottery"}, {"$set": {"message_id": message.id}})
        await interaction.response.send_message("Lottery created successfully.", ephemeral=True)
        

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id != lottery_entry:
            return
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author.id != 270904126974590976:
            return
        content = await self.extract(message)
        content = " ".join(content)
        if "successfully donated" not in content.lower():
            return
        if "⏣" in content:
            doc = collection.find_one({"_id": "lottery"})
            if not doc:
                await message.reply("There is no ongoing lottery, please contact an admin for a refund.")
                return
            amount = content.split("**")[1]
            amount = amount.replace("⏣ ", "")
            amount = amount.replace(",", "")
            amount = int(amount)
            entry = doc["entry"]
            entries = amount // entry
            if entries < 1:
                await message.reply(f"Invalid donation, one entry costs ⏣ {entry:,}.")
                return
            collection.update_one({"_id": "lottery"}, {"$inc": {f"entries.{message.interaction.user.id}": entries, "pool": amount}})
            embed = nextcord.Embed(
                title="Lottery Entries Added",
                description=f"**Entries** | `{entries:,}`\n**Donated** | `⏣ {amount:,}`\n**Cost Per Entry** | `⏣ {entry:,}`\n**Entrant** | {message.interaction.user.mention}",
                color=nextcord.Color.blurple()
            )
            embed.set_footer(text=f"Robbing Central Lotteries", icon_url=message.guild.icon.url)
            await message.reply(content=f"{message.interaction.user.mention}", embed=embed)
            log_channel = message.guild.get_channel(lottery_logs)
            doc = collection.find_one({"_id": "lottery"})
            total_entries = sum(doc["entries"].values())
            embed.description = f"**Total Entries:** | `{total_entries:,}`\n**Entries** | `{entries:,}`\n**Donated** | `⏣ {amount:,}`\n**Cost Per Entry** | `⏣ {entry:,}`\n**Entrant** | {message.interaction.user.mention}"
            await log_channel.send(embed=embed)
            await message.add_reaction(GREEN_CHECK)
        else:
            await message.reply("Invalid donation, only coins are accepted for lotteries.", mention_author=False)


def setup(bot):
    bot.add_cog(Lottery(bot))
import nextcord
from nextcord.ext import commands, tasks
import asyncio
from typing import Dict, Any, List
from datetime import datetime

AUCTION_CHANNEL = 1240782193270460476
DANK_ID = 270904126974590976
GREEN_CHECK = "<:green_check:1218286675508199434>"
RED_X = "<:red_x:1218287859963007057>"
GREEN = 65280
GRAY = 8421504
VALID_FIELDS = ["asset", "seller", "buyer", "price", "image", "img"]


from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Auction"]
itemcollection = db["Items"]
configuration = db["Configuration"]
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

class Use(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

class Auction(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.sticky_bid_locks = {}
        self.guide_locks = {}
        self.extractor = PrecisionExtractor()
        self.queue_payout_lock = asyncio.Lock()
        
    def get_guild_lock(self, guild_id, lock_dict):
        if guild_id not in lock_dict:
            lock_dict[guild_id] = asyncio.Lock()
        return lock_dict[guild_id]
    
    def cog_unload(self):
        if self.cache_auction.is_running():
            self.cache_auction.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.cache_auction.is_running():
            self.cache_auction.start()
        self.bot.add_view(Use())
        print("Auction cog loaded.")

    @tasks.loop(seconds=30)
    async def cache_auction(self):
        config = configuration.find_one({"_id": "config"})
        self.cache = config["auction"]

    async def extract(self, message):
        target = message
        route = nextcord.http.Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=target.channel.id, message_id=target.id
        )
        raw_json = await self.bot.http.request(route)
        content_pieces = self.extractor.extract_content(raw_json)
        return content_pieces

    @commands.command(name="auction")
    async def auction_handler(self, message):
        try:
            doc = configuration.find_one({"_id": "config"})
            old_doc = doc
            doc = doc["auction_manager"]
            guild = str(message.guild.id)
            if guild not in doc:
                return
            else:
                manager = doc[guild]
            roles = [role.id for role in message.author.roles]

            channel = old_doc["auction"]
            if guild not in channel:
                return
            else:
                auction_channel = channel[guild]

            if message.channel.id != auction_channel:
                return

            if not any(role in manager for role in roles):
                await message.message.add_reaction(RED_X)
                return
            if len(message.message.content.split(" ")) == 1:
                if collection.find_one({"_id": message.channel.id}):
                    await message.message.add_reaction(RED_X)
                    return
                await self.auction(message.message)
                return
            arg = message.message.content.split(" ")[1].lower()
            if arg == "set":
                await self.set_auction(message)
                return
            elif arg == "end":
                await self.end_auction(message)
                return
        except:
            return
    @commands.Cog.listener()
    async def on_message(self, message):
        try:
            auction_channel = self.cache.get(str(message.guild.id))
        except:
            return
        split = message.content.split(" ")
        if not auction_channel:
            return
        if message.channel.id != auction_channel:
            return

        if message.author.id == self.bot.user.id:
            if message.embeds:
                if message.embeds[0].description:
                    if "Asset" in message.embeds[0].description or "auction" in message.embeds[0].description.lower():
                        return
            elif message.content:
                if "locked" in message.content.lower():
                    return
                
        if message.content.startswith("!auction") or message.content.startswith("-auction") or message.content.startswith(".auction"):
            return
        elif "<@&1241563195731349504>" in message.content.lower():
            await self.unlock(message)
            return 
        elif not collection.find_one({"_id": message.channel.id}):
            await self.guide(message)
            return
        elif any(char.isdigit() for char in message.content) and "<:" not in message.content:
            if len(split) > 1:
                await self.sticky_bid(message)
                return
            elif message.content.lower() not in ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]:
                await self.bid(message)
                return
            else:
                await self.sticky_bid(message)
                return
        else:
            await self.sticky_bid(message)
            return
        
    async def sticky_bid(self, message):
        guild_lock = self.get_guild_lock(message.guild.id, self.sticky_bid_locks)
        async with guild_lock:
            channel_id = message.channel.id
            auction_data = collection.find_one({"_id": channel_id}, {"Seller": 1, "Asset": 1, "Price": 1, "Buyer": 1, "Image": 1, "Value": 1, "Sticky": 1})
            buyer = f"<@{auction_data['Buyer']}>" if auction_data['Buyer'] else "None"
            embed = nextcord.Embed(
                title="Auction Ongoing",
                description=(
                    f"`Asset` | {auction_data['Asset']} \n"
                    f"`Seller` | <@{auction_data['Seller']}> \n"
                    f"`Buyer` | {buyer} \n"
                    f"`Price` | ⏣ {auction_data['Price']:,}\n"
                    f"`Item Value` | ⏣ {auction_data['Value']:,}"
                ),
                color=GRAY
            ).set_thumbnail(url=auction_data['Image']).set_footer(text="Is it worth it?")
            try:
                response = await message.channel.send(embed=embed)
                asyncio.create_task(self.delete_sticky(message, auction_data["Sticky"]))
            except:
                embed.set_thumbnail(url=None)
                response = await message.channel.send(embed=embed)
            collection.update_one({"_id": channel_id}, {"$set": {"Sticky": response.id}})

    async def guide(self, message):
        guild_lock = self.get_guild_lock(message.guild.id, self.guide_locks)
        async with guild_lock:
            guild_id = str(message.guild.id)
            try:
                id = collection.find_one({"_id": 1234567890})[f"Guide"][guild_id]
            except:
                id = None
            asyncio.create_task(self.delete_sticky(message, id))
            embed = None
            if message.guild.id == 1205270486230110330:
                embed = nextcord.Embed(
                title="Guidelines",
                description=f"❔ In an auction, you bid for an asset, typically items. The highest bidder gets the asset and pay their own offer to the seller. \n- Asset must be worth ⏣ 30,000,000 minimum. \n- Bets must be in increments of ⏣ 50,000 or above. \n- Sell one type of item at a time. Always bid in coins. \n- Coin transactions and failed sales are taxed 5% of their value. \n- Do not troll. Chat at your own risk. \nDo `-auction` in <#1205270487454974055> if you are interested.",
                color=GRAY
                )
            else:
                embed = nextcord.Embed(
                title="Guidelines",
                description=f"❔ In an auction, you bid for an asset, typically items. The highest bidder gets the asset and pay their own offer to the seller. \n- Sell one type of item at a time. Always bid in coins. \n- Do not troll. Chat at your own risk. \n- Bid in increments of ⏣ 50,000 or above.",
                color=GRAY
                )
            embed.set_footer(text="Failure to pay a placed offer will result in a severe punishment.")
            response = await message.channel.send(embed=embed)
            collection.update_one({"_id": 1234567890}, {"$set": {f"Guide.{guild_id}": response.id}}, upsert=True)

    async def delete_sticky(self, message, id):
        try:
            await message.channel.delete_messages([nextcord.Object(id=id)])
        except:
            pass
            
    async def end_auction(self, message):
        doc = configuration.find_one({"_id": "config"})
        auction_role = doc["auction_role"]
        lock_on_end = doc["auction_lock_on_end"]
        try:
            last_bid = doc["last_bid"]
        except:
            last_bid = 0
        guild = str(message.guild.id)
        time = int(datetime.now().timestamp())
        if time - last_bid < 5:
            await message.message.add_reaction(RED_X)
            return
        if guild not in lock_on_end:
            lock_on_end = False
        else:
            lock_on_end = lock_on_end[guild]
        
        if guild not in auction_role:
            auction_role = None
        else:
            auction_role = auction_role[guild]
        
        if lock_on_end:
            await message.channel.set_permissions(message.guild.default_role, send_messages=False)
            await message.channel.send(f":white_check_mark: Locked **{message.channel.name}**")
        
        data = collection.find_one({"_id": message.channel.id})
        Buyer = data["Buyer"] or 270904126974590976
        Seller = data["Seller"]
        Asset = data["Asset"]
        Price = data["Price"]
        Image = data["Image"]
        Seller_Tax = int(Price * 0.95)
        Price = int(Price)

        embed = nextcord.Embed(
            title="Auction Concluded",
            description=(
                f"This auction has been concluded. \n"
                f"{Asset} was sold to <@{Buyer}> for ⏣ {Price:,}. \n\n"
                f"The seller (<@{Seller}>) was taxed 5% and will receive ⏣ {Seller_Tax:,}."
            ),
            color=GREEN
        ).set_thumbnail(url=Image).set_footer(text="Thank you for participating!")

        sticky = data.get("Sticky")
        try:
            await message.channel.delete_messages([nextcord.Object(id=sticky)])
        except:
            pass
        
        buyer_member = await message.guild.fetch_member(Buyer)
        if auction_role:
            try:
                await buyer_member.add_roles(nextcord.utils.get(message.guild.roles, id=auction_role))
            except:
                pass
        quan, item = Asset.split(" ", 1)
        queued = False

        async def button_callback(interaction: nextcord.Interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal queued
            nonlocal quan
            if queued:
                return
            queued = True
            if not interaction.user.guild_permissions.manage_messages:
                return
            payout = doc["payout"]
            root = doc["root"]
            queue = doc["queue"]
            claim = doc["claim"]
            if guild not in payout or guild not in root or guild not in queue or guild not in claim:
                await interaction.send("Payouts system is not configured for this guild. Please set up via `/config`", ephemeral=True)
                return
            payouts_cog = self.bot.get_cog("payouts")
            quan = quan.replace(",", "")
            args = [int(Buyer), int(quan), item, interaction.message.id, "auction"]
            if payouts_cog:
                embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for 2 winners.")
                embed.set_footer(text=f"This time may vary depending on the amount of winners.")
                embed.color = nextcord.Color.yellow()
                msg = await interaction.send(embed=embed, ephemeral=True)
                buyer_args = [int(Buyer), int(quan), item, interaction.message.id, "auction"]
                seller_args = [int(Seller), int(Seller_Tax), None, interaction.message.id, "auction"]
                await asyncio.gather(
                    payouts_cog.auction_payout(buyer_args, interaction),
                    payouts_cog.auction_payout(seller_args, interaction)
                )
                embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
                embed.color = 65280
                view = nextcord.ui.View()
                queue = doc["queue"][guild]
                view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{interaction.guild.id}/{queue}/", emoji="🔗"))
                await msg.edit(embed=embed, view=view)
                await interaction.message.edit(view=None)
                await response.add_reaction("<a:loading_animation:1218134049780928584>")
                await interaction.channel.send(f"<@{Buyer}>, <@{Seller}> your payouts have been queued, you do not need to claim them.")
                if auction_role is not None:
                    try:
                        await buyer_member.remove_roles(nextcord.utils.get(message.guild.roles, id=auction_role))
                    except:
                        pass
            else:
                await interaction.send("Payouts cog is not loaded. Please queue manually.", ephemeral=True)
            

        view = nextcord.ui.View()
        button = nextcord.ui.Button(label="Queue Payouts", style=nextcord.ButtonStyle.primary, custom_id="payout_callback")
        button.callback = button_callback
        view.add_item(button)
        
        response = await message.channel.send(content=f"<@{Buyer}> you have won the auction! Please pay `⏣ {Price:,}` using `/serverevents donate`", embed=embed, view=view)
        
        await message.message.add_reaction(GREEN_CHECK)
        collection.delete_one({"_id": message.channel.id})
        
        await asyncio.sleep(3)
        await response.clear_reactions()
        await asyncio.sleep(300)
        if auction_role:
            try:
                await buyer_member.remove_roles(nextcord.utils.get(message.guild.roles, id=auction_role))
            except:
                pass
        collection.delete_one({"_id": response.id})


    async def bid(self, message):
        guild_lock = self.get_guild_lock(message.guild.id, self.sticky_bid_locks)
        async with guild_lock:
            doc = collection.find_one({"_id": message.channel.id})
            if not doc:
                return
            amount = message.content.replace(',', '').lower()
            multipliers = {'k': 1000, 'm': 1_000_000, 'b': 1_000_000_000, 't': 1_000_000_000_000}
            if amount[-1] in multipliers:
                try:
                    amount = int(float(amount[:-1]) * multipliers[amount[-1]])
                except ValueError:
                    return
            else:
                try:
                    amount = int(amount)
                except ValueError:
                    return
            
            current_price = doc["Price"]
            if amount < current_price or abs(amount - current_price) <= 50_000 or amount >= 10_000_000_000:
                await message.add_reaction(RED_X)
                return
            
            embed = nextcord.Embed(
                title="Price Updated",
                description=(
                    f"`Asset` | {doc['Asset']} \n"
                    f"`Seller` | <@{doc['Seller']}> \n"
                    f"`Buyer` | {message.author.mention} \n"
                    f"`Price` | ⏣ {amount:,}\n"
                    f"`Item Value` | ⏣ {doc['Value']:,}"
                ),
                color=65280
            ).set_thumbnail(url=doc["Image"]).set_footer(text="Is it worth it?")
            
            response = await message.channel.send(embed=embed)
            asyncio.create_task(self.delete_sticky(message, doc["Sticky"]))
            time = int(datetime.now().timestamp())
            collection.update_one({"_id": message.channel.id}, {"$set": {"Price": amount, "Buyer": message.author.id, "Sticky": response.id, "last_bid": time}})
            await message.add_reaction(GREEN_CHECK)
            

    async def set_auction(self, message):
        if not message.author.guild_permissions.manage_messages:
            return
        
        doc = collection.find_one({"_id": message.channel.id})
        if doc is None:
            await message.reply(content="There is no active auction in this channel.", mention_author=False)
            return
        
        strip_msg = message.message.content.split("auction set ")[1]
        type = strip_msg.split(" ")[0]
        action = " ".join(strip_msg.split(" ")[1:])
        strip_msg = type.lower()
        if strip_msg not in VALID_FIELDS:
            return
        elif strip_msg == "img":
            type = "image"
        elif strip_msg == "value":
            type = "value"
            action = action.split(" ")[0]
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = action.lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(action[:-1])
                    multiplier = multipliers[action[-1]]
                    action = int(numeric_part * multiplier)
                except ValueError:
                    return
            else:
                if ',' in action:
                    action = action.replace(',', '')
            try:
                action = int(action)
            except ValueError:
                return
        elif strip_msg == "price":
            action = action.split(" ")[0]
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = action.lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(action[:-1])
                    multiplier = multipliers[action[-1]]
                    action = int(numeric_part * multiplier)
                except ValueError:
                    return
            else:
                if ',' in action:
                    action = action.replace(',', '')
            try:
                action = int(action)
            except ValueError:
                return
        elif strip_msg == "asset":
            quan = action.split(" ")[0]

            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            if quan[-1] in multipliers:
                try:
                    numeric_part = float(quan[:-1])
                    multiplier = multipliers[quan[-1]]
                    quan = int(numeric_part * multiplier)
                except ValueError:
                    return
            else:
                if ',' in quan:
                    quan = quan.replace(',', '')
            try:
                quan = int(quan)
            except ValueError:
                return
            

            item = action.split(" ")[1:]
            item = " ".join(item)
            get_item = await self.bot.get_cog("Calculator").item_finder(item)
            if not get_item:
                get_item = item
            else:
                try:
                    value = itemcollection.find_one({"_id": get_item})
                    value = value["price"]
                    value = value * quan
                    collection.update_one({"_id": message.channel.id}, {"$set": {"Value": value}})
                except:
                    pass

            action = f"{quan:,} {get_item}"
        type = type.capitalize()
        try:
            action = action.replace("<", "")
            action = action.replace(">", "")
            action = action.replace("@", "")
        except:
            pass
        collection.update_one({"_id": message.channel.id}, {"$set": {type: action}})
        await message.message.add_reaction(GREEN_CHECK)
        embed = nextcord.Embed(title="Value Override", description=f"Database successfully updated for `{type.lower()}` by {message.author.mention}.")
        embed.color = GRAY
        embed.set_footer(text="Changes will take effect upon interaction.")
        await message.channel.send(embed=embed)

    async def auction(self, message):
        if not message.reference:
            await message.add_reaction(RED_X)
            return
        else:
            try:
                msg_id = message.reference.message_id
                msg = await message.channel.fetch_message(msg_id)
            except Exception as e:
                print(e)
                await message.add_reaction(RED_X)
                return
        content_pieces = await self.extract(msg)
        if not content_pieces:
            await message.add_reaction(RED_X)
            return
        content = " ".join(content_pieces)
        if "successfully donated" not in content.lower():
            await message.add_reaction(RED_X)
            return
        elif "⏣" in content.lower():
            await message.add_reaction(RED_X)
            return
        if GREEN_CHECK in msg.reactions:
            await message.add_reaction(RED_X)
            return
        else:
            seller = msg.interaction.user.id
            await message.add_reaction(GREEN_CHECK)
            await self.start_auction(msg, message.channel.id, seller)
        
    
    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        try:
            auction_channel = self.cache.get(str(payload.guild_id))
            if not auction_channel:
                return
            elif payload.channel_id != auction_channel:
                return
            
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
            if message.author.id != DANK_ID:
                return
            
            content_pieces = await self.extract(message)
            if not content_pieces:
                return
            content = " ".join(content_pieces)
            if "successfully donated" not in content.lower():
                return
            elif "⏣" in content.lower():
                return
            
            seller = message.interaction.user.id
            check = collection.find_one({"_id": message.channel.id})
            if check:
                return
            await message.add_reaction(GREEN_CHECK)
            await self.start_auction(message, message.channel.id, seller)
        except Exception as e:
            print(e)
            return

    async def start_auction(self, message, channel_id, seller):
        collection2 = db["Items"]
        channel = self.bot.get_channel(channel_id)
        await message.add_reaction(GREEN_CHECK)
        content_pieces = await self.extract(message)
        if not content_pieces:
            return
        content = " ".join(content_pieces)  
        print("1")
        emoji = content.split(" ")[3]
        amt = content.split(" ")[2]
        amt = amt.replace(",", "")
        amt = amt.replace("*", "")
        amt = int(amt)
        print(amt)
        item = content.split("> ")[1]
        item = item.replace("*", "")
        print(item)
        if emoji.startswith("<a"):
            ending = "gif"
        else:
            ending = "png"
        emoji = emoji.split(":")[2]
        emoji = emoji.replace(">", "")
        emoji = f"https://cdn.discordapp.com/emojis/{emoji}.{ending}?size=2048"
        print("2")
        embed = nextcord.Embed(title=f"Auction Started")
        item_value = collection2.find_one({"_id": item})
        print("3")
        if not item_value:
            item_value = "Unknown"
        else:
            item_value = item_value["price"]
            item_value = amt * item_value
        print("4")
        collection.insert_one({"_id": channel_id, "Asset": f"{amt} {item}", "Seller": seller, "Buyer": None, "Price": 1, "Image": emoji, "Sticky": False, "Value": item_value})
        print("5")
        embed.description = f"`Asset` | {amt} {item} \n `Seller` | <@{seller}> \n `Buyer` | None \n `Price` | ⏣ 1 \n `Item Value` | ⏣ {item_value:,}"
        print("6")
        embed.set_thumbnail(url=emoji)
        print("7")
        embed.set_footer(text=f"Is it worth it?")
        print("8")
        embed.color = GRAY
        print("9")
        await channel.send(embed=embed)
        print("10")

    async def unlock(self, message):
        overwrites = message.channel.overwrites_for(message.guild.default_role)
        if overwrites.send_messages is True or overwrites.send_messages is None:   
            return
        overwrites.send_messages = None
        await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
        await message.channel.send(f":white_check_mark: Unlocked **{message.channel.name}**")
        await asyncio.sleep(1)

def setup(bot):
    bot.add_cog(Auction(bot))   

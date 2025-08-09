from typing import Any, Dict, List
import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["RC Donations"]
items = db["Items"]

DONATION_CHANNEL = 1205270487454974055
DANK_ID = 270904126974590976

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

class Donations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Donations cog loaded")
        self.precision_extractor = PrecisionExtractor()


    async def extract(self, message):
        target = message
        route = nextcord.http.Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=target.channel.id, message_id=target.id
        )
        raw_json = await self.bot.http.request(route)
        content_pieces = self.precision_extractor.extract_content(raw_json)
        return content_pieces

    @commands.Cog.listener()
    async def on_raw_message_edit(self, payload):
        if payload.channel_id != DONATION_CHANNEL:
            return
        
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        if message.author.id != DANK_ID:
            return
        
        content = await self.extract(message)
        content = " ".join(content)
        if "successfully donated" not in content.lower():
            return
        if "⏣" in content:
            amount = content.split("**")[1]
            amount = amount.replace("⏣ ", "")
            amount = amount.replace(",", "")
            amount = int(amount)
            user_id = message.interaction.user.id
            collection.update_one({"_id": "rc_donations"}, {"$inc": {f"Regular.{user_id}": amount}}, upsert=True)
            await message.add_reaction(GREEN_CHECK)
            embed = nextcord.Embed(
                title="Donation Logged",
                description=f"Successfully added **⏣ {amount:,}** to Regular donations.",
                color=0x57F287
            )
            await message.channel.send(embed=embed)
        else:
            amount = content.split("**")[1]
            first = amount.split("<")[0]
            second = amount.split("> ")[1]
            second = second.strip()
            first = first.replace(",", "")
            first = int(first)
            item = items.find_one({"_id": second})
            value = item["value"]
            total_added = value * first
            user_id = message.interaction.user.id
            collection.update_one({"_id": "rc_donations"}, {"$inc": {f"Regular.{user_id}": total_added}}, upsert=True)
            await message.add_reaction(GREEN_CHECK)
            embed = nextcord.Embed(
                title="Donation Logged",
                description=f"Successfully added **⏣ {total_added:,}** to Regular donations from {first:,}x {second}.",
                color=0x57F287
            )
            await message.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Donations(bot))
import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection
from typing import Dict, List, Any

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

    @commands.Cog.listener()
    async def on_ready(self):
        print("Lottery cog loaded.")

    async def extract(self, message):
        target = message
        route = nextcord.http.Route(
            'GET', '/channels/{channel_id}/messages/{message_id}',
            channel_id=target.channel.id, message_id=target.id
        )
        raw_json = await self.bot.http.request(route)
        content_pieces = self.extractor.extract_content(raw_json)
        return content_pieces

    @nextcord.slash_command(name="lottery")
    async def lottery(self, interaction: nextcord.Interaction):
        pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id != lottery_entry:
            return
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
            collection.update_one({"_id": "lottery"}, {"$inc": {f"entries.{message.author.id}": entries}})
            await message.add_reaction(GREEN_CHECK)


def setup(bot):
    bot.add_cog(Lottery(bot))
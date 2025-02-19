import nextcord
import json
import re

from nextcord.ext import commands
from nextcord import SlashOption
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Items"]

class Calculator(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Calculator cog loaded")

    @nextcord.slash_command(name="itemcalc", description="Calculate the value of an item(s).")
    async def itemcalc(self, interaction: nextcord.Interaction, item: str = SlashOption(description="The item(s) to calculate. Format: [quantity] [item name]")):
        item = item.lower()
        await interaction.response.defer(ephemeral=False)
        items = re.split(r'(?:^|\s)(?=\d+(?:[k|m|b|t])?\s)', item)
        items = [i.strip() for i in items if i.strip()]
        grand_total = 0
        item_descp = ""
        for strip_item in items:
            split_item = strip_item.split()
            try:
                quantity = split_item[0]
                item_name = split_item[1:]
            except:
                await interaction.send(f"Unable to parse item: `{strip_item}`", ephemeral=False)
                return
            quantity = quantity.replace("k", "000").replace("m", "000000").replace("b", "000000000").replace("t", "000000000000")
            quantity = int(quantity)
            item_name = " ".join(item_name)
            name = await self.item_finder(item_name.lower())
            if name is None:
                await interaction.send(f"Unable to find item: `{item_name}`", ephemeral=False)
                return
            price = collection.find_one({"_id": name})["price"]
            total = price * quantity
            grand_total += total
            item_descp = f"{item_descp}\n`{quantity}x` {name} - ⏣ {total:,}"
        embed = nextcord.Embed(title="Item Calculator", color=nextcord.Color.blurple())
        embed.add_field(name="Items", value=item_descp)
        embed.add_field(name="Amount", value=f"```Amount: ⏣ {grand_total:,}\nRaw: {grand_total}```", inline=False)
        await interaction.followup.send(embed=embed, ephemeral=False)
        
    async def item_finder(self, item_name):
        all_items = collection.find({})
        all_items = [item["_id"] for item in all_items if isinstance(item["_id"], str)]
        
        cleaned_input = item_name.replace(",", "").replace("'", "").lower()

        for item in all_items:
            if cleaned_input == item.lower():
                return item
        
        for item in all_items:
            item_words = item.lower().split()
            if cleaned_input in item_words:
                return item
        
        best_match = process.extractOne(
            cleaned_input,
            all_items,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=75
        )
        
        if best_match:
            return best_match[0]
            
        if len(cleaned_input) > 3:
            for item in all_items:
                if cleaned_input in item.lower():
                    return item
        best_match = process.extractOne(
            cleaned_input,
            all_items,
            scorer=fuzz.partial_ratio,
            score_cutoff=69
        )

        if not best_match:
            if len(cleaned_input) >= 3:
                matches = [item for item in all_items if item.lower().startswith(cleaned_input)]
                if matches:
                    return min(matches, key=len)
                
        if not best_match:
            best_match = process.extractOne(
            cleaned_input,
            all_items,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=50
        )
                
        if not best_match:
            best_match = process.extractOne(
            cleaned_input,
            all_items,
            scorer=fuzz.partial_ratio,
            score_cutoff=35
        )


        if best_match:
            return best_match[0]
        return None


    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if not message.content or message.author.bot:
            return
        content = message.content
        if len(content.split()) != 1:
            return
        args = ["+", "-", "*", "/", "^", "%"]
        if not any(arg in content for arg in args):
            return
        content = content.replace(",", "")
        await self.calculator(message, content)

    async def calculator(self, message, content):
        numbers = re.split(r'[+\-*/^%]', content)
        for number in numbers:
            if "k" in number:
                old_number = number.replace("k", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000
                content = content.replace(number, str(old_number))
            elif "m" in number:
                old_number = number.replace("m", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000
                content = content.replace(number, str(old_number))
            elif "b" in number:
                old_number = number.replace("b", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000000
                content = content.replace(number, str(old_number))
            elif "t" in number:
                old_number = number.replace("t", "")
                try:
                    old_number = float(old_number)
                except:
                    return
                old_number = old_number * 1000000000000
                content = content.replace(number, str(old_number))
        
        if "%" in content:
            parts = re.split(r'(\d+(?:\.\d+)?%|\+|\-|\*|\/|\^)', content)
            parts = [p.strip() for p in parts if p.strip()]
            
            for i, part in enumerate(parts):
                if part.endswith('%'):
                    number = float(part[:-1]) / 100
                    parts[i] = str(number)
            
            content = ''.join(parts)
        
        content = content.replace('^', '**')
        
        try:
            result = eval(content)
            result = float(result)
            raw = result
            if result.is_integer():
                raw = f"{int(result)}.0"
            else:
                raw = f"{result}"
        except:
            return
        solved_result = f"{result:,.2f}"
        embed = nextcord.Embed(description=f"**Solved:** `{solved_result}`\n**Raw:** `{raw}`")
        embed.set_author(name=f"Calculated {(solved_result)}")
        await message.channel.send(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Calculator(bot))



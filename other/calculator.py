import nextcord
import re

from nextcord.ext import commands
from nextcord import SlashOption
from fuzzywuzzy import fuzz
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
            try:
                quantity = int(quantity)
            except:
                await interaction.send(f"Unable to parse quantity: `{quantity}`", ephemeral=False)
                return
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
        cleaned_input = cleaned_input.replace("dev", "developer").replace("adv", "adventure")
        item_dict_simple = {}
        item_dict_partial = {}
        the_item = None

        for item in all_items:
            if item.lower() == cleaned_input:
                the_item = item
                break

        if the_item is not None:
            return the_item
        
        for item in all_items:
            ratio = fuzz.ratio(item.lower(), cleaned_input)
            ratio2 = fuzz.partial_ratio(item.lower(), cleaned_input)
            if ratio > 90:
                item_dict_simple[item] = ratio
            item_dict_partial[item] = ratio2

        item_dict_simple = sorted(item_dict_simple.items(), key=lambda x: x[1], reverse=True)
        item_dict_partial = sorted(item_dict_partial.items(), key=lambda x: x[1], reverse=True)
        if len(item_dict_simple) > 0:
            the_item = item_dict_simple[0][0]
            return the_item

        for item in all_items:
            if len(cleaned_input.split(" ")) > 1 and len(item.split(" ")) > 1:
                if cleaned_input.split(" ")[0] in item.split(" ")[0] and cleaned_input.split(" ")[1] in item.split(" ")[1]:
                    the_item = item
                    break

        if the_item is not None:    
            return the_item
        
        if len(item_dict_partial) > 0:
            the_item = item_dict_partial[0][0]
            return the_item
        
        return None
    
    @commands.command(name="testfuzz")
    async def testfuzz(self, ctx):
        content = ctx.message.content.split(' ', 1)[1]
        args = re.findall(r'"([^"]*)"', content)
        if len(args) != 2:
            await ctx.send("Please provide exactly two quoted arguments. Example: !testfuzz \"first\" \"second\"")
            return
        response = f"Simple Ratio: {fuzz.ratio(args[0], args[1])}\nPartial Ratio: {fuzz.partial_ratio(args[0], args[1])}\nToken Sort Ratio: {fuzz.token_sort_ratio(args[0], args[1])}\nToken Set Ratio: {fuzz.token_set_ratio(args[0], args[1])}"
        await ctx.send(response)

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
        elif content.startswith("-") or content.startswith("+"):
            return
        elif "%" in content and not any(arg in content for arg in args):
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



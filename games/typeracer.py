import nextcord
import asyncio
import aiohttp
import random
import io

from fuzzywuzzy import fuzz
from datetime import datetime
from nextcord.ext import commands
from PIL import Image, ImageDraw, ImageFont

GREEN_CHECK = "<:green_check2:1291173532432203816>"

class Typeracer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Typeracer Cog has been loaded")

    @commands.command(name="typeracer", aliases=["tr"])
    async def typeracer(self, ctx):
        if ctx.channel.id in self.cache:
            await ctx.reply("There is already a game in progress in this channel.")
            return
        else:
            await self.start_game(ctx)

    async def start_game(self, ctx):
        quote_data = await self.get_quote()
        if not quote_data:
            await ctx.reply("API Failure. Please try again later.")
            return
        quote = quote_data["content"]
        author = quote_data["author"]
        data = await self.get_image(quote)
        if not data:
            await ctx.reply("API Failure. Please try again later.")
            return
        image_binary, color = data
        time = None
        try:
            file = nextcord.File(fp=image_binary, filename='quote.png')
            embed = nextcord.Embed(color=color)
            embed.set_image(url="attachment://quote.png")
            embed.set_footer(text=f"Author: {author}")
            message = await ctx.send(file=file, embed=embed)
            time = datetime.now()
            self.cache[ctx.channel.id] = {"quote": quote, "message": message, "time": time}
        finally:
            image_binary.close()
        await asyncio.sleep(60)
        cache = self.cache.get(ctx.channel.id)
        if cache:
            if cache["time"] == time:
                embed = nextcord.Embed(description="No one finished the quote in time.", color=nextcord.Color.red())
                await message.reply(embed=embed)
                self.cache.pop(ctx.channel.id)

    async def get_quote(self):
        quote_data = None
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://zenquotes.io/api/random") as r:
                    quotes = await r.json()
                    quote_data = {"content": quotes[0]["q"], "author": quotes[0]["a"]}
                    return quote_data
        except aiohttp.ClientConnectionError:
            pass
        if not quote_data:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get("https://api.quotable.io/random") as r:
                        quotes = await r.json()
                        quote_data = {"content": quotes[0]["content"], "author": quotes[0]["author"]}
                        return quote_data
            except aiohttp.ClientConnectionError:
                return None

    async def get_image(self, quote):
        image = Image.new('RGBA', (1, 1), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("times.ttf", 40)
        except:
            font = ImageFont.load_default()
        
        COLORS = [
            (135, 206, 235, 255),
            (230, 190, 255, 255),
            (144, 238, 144, 255),
            (255, 255, 153, 255),
            (255, 178, 102, 255),
            (255, 182, 193, 255),
            (255, 102, 102, 255),
            (255, 255, 255, 255),
        ]
        
        color = random.choice(COLORS)
        padding = 20
        line_height = 50
        
        words = quote.split()
        lines = []
        current_line = []
        max_width = 0
        
        for word in words:
            current_line.append(word)
            text = ' '.join(current_line)
            bbox = draw.textbbox((0, 0), text, font=font)
            width = bbox[2] - bbox[0]
            max_width = max(max_width, width)
            
            if width > 800 - (padding * 2):
                current_line.pop()
                lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
            bbox = draw.textbbox((0, 0), ' '.join(current_line), font=font)
            max_width = max(max_width, bbox[2] - bbox[0])
        
        width = min(800, max_width + (padding * 2))
        height = (len(lines) * line_height) + (padding * 2)
        image = Image.new('RGBA', (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        y = padding
        for line in lines:
            draw.text((padding, y), line, fill=color, font=font)
            y += line_height
        
        image_binary = io.BytesIO()
        image.save(image_binary, 'PNG')
        image_binary.seek(0)
        
        return [image_binary, nextcord.Color.from_rgb(*color[:3])]

    async def check_typeracer(self, message, time):
        cache = self.cache.get(message.channel.id)
        if not cache:
            return
        quote = cache["quote"]
        msg = cache["message"]
        con = message.content
        accuracy = fuzz.ratio(quote, con) / 100
        if accuracy > 0.95:
            self.cache.pop(message.channel.id)
            await message.add_reaction(GREEN_CHECK)
            time_completed = (time - cache["time"]).total_seconds()
            wpm = len(con.split()) / time_completed * 60
            embed = nextcord.Embed(description=f"The race is over! Here are the results:\n1. {message.author.mention} [finished the quote]({msg.jump_url}) in `{time_completed:.2f}s` with an accuracy of **{accuracy * 100:.2f}%**. (**{wpm:.2f} WPM**)", color=nextcord.Color.green())
            await msg.reply(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif message.channel.id not in self.cache:
            return
        time = datetime.now()
        async with self.lock:
            await self.check_typeracer(message, time)

def setup(bot):
    bot.add_cog(Typeracer(bot))
    
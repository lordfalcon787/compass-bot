import nextcord
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection
import random
import json
import asyncio
from PIL import Image, ImageDraw, ImageFont
import io

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Wordle"]

with open('words.json') as f:
    WORD_LIST = json.load(f)

with open('valid_words.json') as f:
    VALID_WORDS = json.load(f)

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lock = asyncio.Lock()
        self.active_games = {}

    @tasks.loop(hours=1)
    async def update_cache(self):
        docs = collection.find({})
        for doc in docs:
            id = doc["_id"]
            doc.pop("_id")
            self.active_games[id] = doc

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Wordle cog loaded.")
        await self.update_cache()

    async def new_wordle(self,message):
        channel_id = message.channel.id
        if channel_id in self.active_games:
            await message.reply("A wordle game is already active in this channel! Use 'end wordle' to stop it.")
            return
        word = random.choice(WORD_LIST)
        self.active_games[channel_id] = {'word': word, 'guesses': []}
        collection.insert_one({"_id": channel_id, "word": word, "guesses": []})
        await message.reply("A new wordle game has been started! Type `guess [your guess]` to start playing!")

    async def end_wordle(self,message):
        channel_id = message.channel.id
        if channel_id not in self.active_games:
            await message.reply("No active Wordle game in this channel.")
            return
        word = self.active_games[channel_id]['word']
        del self.active_games[channel_id]
        collection.delete_one({"_id": channel_id})
        await message.reply(f"Ended the current game. The word was: **{word.upper()}**")

    def create_wordle_image(self, guesses, answer):
        box_size = 400
        spacing = 40
        font_size = 240
        width = box_size * 5 + spacing * 6
        height = (box_size + spacing) * len(guesses) + spacing
        green = (11, 102, 35)
        yellow = (221, 159, 33)
        gray = (43 , 43, 45)
        white = (215, 218, 220)
        black = (0, 0, 0)
        img = Image.new('RGB', (width, height), color=black)
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
        for row, guess in enumerate(guesses):
            answer_chars = list(answer)
            guess_chars = list(guess)
            colors = [gray] * 5
            for i in range(5):
                if guess_chars[i] == answer_chars[i]:
                    colors[i] = green
                    answer_chars[i] = None
            for i in range(5):
                if colors[i] == green:
                    continue
                if guess_chars[i] in answer_chars:
                    colors[i] = yellow
                    answer_chars[answer_chars.index(guess_chars[i])] = None
            for col in range(5):
                x0 = spacing + col * (box_size + spacing)
                y0 = spacing + row * (box_size + spacing)
                x1 = x0 + box_size
                y1 = y0 + box_size
                draw.rectangle([x0, y0, x1, y1], fill=colors[col], outline=None)
                bbox = draw.textbbox((0, 0), guess[col].upper(), font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
                text_x = x0 + (box_size - w) / 2
                text_y = y0 + (box_size - h) / 4
                draw.text((text_x, text_y), guess[col].upper(), font=font, fill=white)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf

    async def guess(self, message):
        channel_id = message.channel.id
        word = message.content.lower().split(" ")[1]
        if channel_id not in self.active_games:
            return
        if len(word) != 5 or word not in VALID_WORDS:
            await message.reply("That is not a valid word.")
            return
        if word in self.active_games[channel_id]['guesses']:
            await message.reply("You already guessed that word.")
            return
        async with self.lock:
            if channel_id not in self.active_games:
                return   
            game = self.active_games[channel_id]
            game['guesses'].append(word)
            answer = game['word']
            image_buf = self.create_wordle_image([word], answer)
            file = nextcord.File(image_buf, filename="wordle.png")
            if word == answer:
                del self.active_games[channel_id]
                points = 10 if len(game['guesses']) == 1 else 7 if len(game['guesses']) == 2 else 5 if len(game['guesses']) == 3 else 3 if len(game['guesses']) == 4 else 2 if len(game['guesses']) == 5 else 1 if len(game['guesses']) == 6 else 0
                await message.reply(file=file, content=f"Correct! You guessed it in **{len(game['guesses'])}** tries. You won **{points}** points.")
                collection.delete_one({"_id": channel_id})
                collection.update_one({"_id": "wordle_stats"}, {"$inc": {f"{message.author.id}.wins": 1}}, {"$inc": {f"{message.author.id}.guesses": 1}}, {"$inc": {f"{message.author.id}.points": points}}, upsert=True)
            else:
                await message.reply(file=file)
                asyncio.create_task(self.update_wordle(channel_id, game, message.author))
    
    async def update_wordle(self, channel_id, game, user):
        collection.update_one({"_id": channel_id}, {"$set": {"guesses": game['guesses']}})
        collection.update_one({"_id": "wordle_stats"}, {"$inc": {f"{user.id}.guesses": 1}}, upsert=True)

    async def wordle_stats(self, message):
        user = message.author.id
        stats = collection.find_one({"_id": "wordle_stats"})
        if not stats:
            await message.reply("No wordle stats found.")
            return
        points = stats.get(user.id, {}).get('points', 0)
        wins = stats.get(user.id, {}).get('wins', 0)
        guesses = stats.get(user.id, {}).get('guesses', 0)
        embed = nextcord.Embed(description=f"- Points: {points}\n- Total Correct Guesses: {wins}\n- Total Guesses: {guesses}\n- Average Guesses per Correct Word: {guesses / wins if wins > 0 else 0}")
        embed.set_author(name=f"{user.name}'s Wordle Stats", icon_url=user.avatar.url)
        embed.set_footer(text="Compass Wordle", icon_url=self.bot.user.avatar.url)
        await message.reply(embed=embed)

    async def wordle_leaderboard(self, message):
        stats = collection.find_one({"_id": "wordle_stats"})
        if not stats:
            await message.reply("No wordle stats found.")
            return
        
        user_stats = [(k, v) for k, v in stats.items() if k != "_id"]
        user_stats.sort(key=lambda x: x[1].get('points', 0), reverse=True)
        
        items_per_page = 10
        pages = []
        
        for i in range(0, len(user_stats), items_per_page):
            page_stats = user_stats[i:i+items_per_page]
            page_content = ""
            
            for idx, (user_id, user_data) in enumerate(page_stats, start=i+1):
                try:
                    user = await self.bot.fetch_user(int(user_id))
                    username = user.name
                except:
                    username = f"User {user_id}"
                
                points = user_data.get('points', 0)
                wins = user_data.get('wins', 0)
                guesses = user_data.get('guesses', 0)
                
                page_content += f"**{idx}. {username}** - {points} points\n"
                page_content += f"   Wins: {wins} | Guesses: {guesses}\n"
            
            embed = nextcord.Embed(
                title="Wordle Leaderboard",
                description=page_content,
                color=nextcord.Color.blue()
            )
            embed.set_footer(text=f"Page {len(pages)+1}/{(len(user_stats)+items_per_page-1)//items_per_page}")
            pages.append(embed)
        
        if not pages:
            embed = nextcord.Embed(
                title="Wordle Leaderboard",
                description="No stats available yet.",
                color=nextcord.Color.blue()
            )
            await message.reply(embed=embed)
            return
        
        class LeaderboardView(nextcord.ui.View):
            def __init__(self, pages):
                super().__init__(timeout=60)
                self.pages = pages
                self.current_page = 0
                
                if len(pages) <= 1:
                    self.clear_items()
                else:
                    self.update_buttons()
            
            def update_buttons(self):
                self.previous_button.disabled = self.current_page == 0
                self.next_button.disabled = self.current_page == len(self.pages) - 1

            @nextcord.ui.button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.blurple, disabled=True)
            async def previous_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                await interaction.response.defer()
                if self.current_page > 0:
                    self.current_page -= 1
                    self.update_buttons()
                    await interaction.message.edit(embed=self.pages[self.current_page], view=self)
            
            @nextcord.ui.button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.blurple)
            async def next_button(self, button: nextcord.ui.Button, interaction: nextcord.Interaction):
                await interaction.response.defer()
                if self.current_page < len(self.pages) - 1:
                    self.current_page += 1
                    self.update_buttons()
                    await interaction.message.edit(embed=self.pages[self.current_page], view=self)
            
            async def on_timeout(self):
                for item in self.children:
                    item.disabled = True
                await self.message.edit(view=self)
        
        view = LeaderboardView(pages)
        view.message = await message.reply(embed=pages[0], view=view)
        
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.content:
            return
        if message.content.lower() == "new wordle":
            asyncio.create_task(self.new_wordle(message))
            return
        elif message.content.lower() == "end wordle":
            asyncio.create_task(self.end_wordle(message))
            return
        elif message.content.lower().startswith("guess "):
            asyncio.create_task(self.guess(message))
            return
        elif message.content.lower() == "wordle stats" or message.content.lower() == "wordle statistics":
            asyncio.create_task(self.wordle_stats(message))
            return
        elif message.content.lower() == "wordle leaderboard" or message.content.lower() == "wordle top":
            asyncio.create_task(self.wordle_leaderboard(message))
            return
        

def setup(bot):
    bot.add_cog(Wordle(bot))
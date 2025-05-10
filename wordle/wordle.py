import nextcord
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection
import random
import json
import os
from PIL import Image, ImageDraw, ImageFont
import io

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Wordle"]

with open('words.json') as f:
    WORD_LIST = json.load(f)

class Wordle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = {}
        self.active_games = {}

    @tasks.loop(hours=1)
    async def update_cache(self):
        docs = collection.find({})
        for doc in docs:
            doc.pop("_id")
            self.cache[doc["_id"]] = doc

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Wordle cog loaded.")
        await self.load_cache()

    async def new_wordle(self,message):
        channel_id = message.channel.id
        if channel_id in self.active_games:
            await message.reply("A Wordle game is already active in this channel! Use 'end wordle' to stop it.", ephemeral=True)
            return
        word = random.choice(WORD_LIST)
        self.active_games[channel_id] = {'word': word, 'guesses': []}
        await message.reply("Wordle game started! Use 'guess [word]' to play.")

    async def end_wordle(self,message):
        channel_id = message.channel.id
        if channel_id not in self.active_games:
            await message.reply("No active Wordle game in this channel.", ephemeral=True)
            return
        word = self.active_games[channel_id]['word']
        del self.active_games[channel_id]
        await message.reply(f"Wordle game ended. The word was: **{word.upper()}**")

    def create_wordle_image(self, guesses, answer):
        box_size = 100
        spacing = 10
        font_size = 60
        width = box_size * 5 + spacing * 6
        height = (box_size + spacing) * len(guesses) + spacing
        green = (83, 141, 78)
        yellow = (181, 159, 59)
        gray = (58, 58, 60)
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
                w, h = draw.textsize(guess[col].upper(), font=font)
                draw.text((x0 + (box_size - w) / 2, y0 + (box_size - h) / 2), guess[col].upper(), font=font, fill=white)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return buf

    async def guess(self, message):
        channel_id = message.channel.id
        word = message.content.lower().split(" ")[1]
        if channel_id not in self.active_games:
            return
        if len(word) != 5 or word not in WORD_LIST:
            await message.reply("Please guess a valid 5-letter word from the word list.", ephemeral=True)
            return
        game = self.active_games[channel_id]
        game['guesses'].append(word)
        answer = game['word']
        guesses = game['guesses']
        image_buf = self.create_wordle_image(guesses, answer)
        file = nextcord.File(image_buf, filename="wordle.png")
        if word == answer:
            del self.active_games[channel_id]
            await message.reply(file=file, content="Congratulations! You guessed the word! 🎉")
        elif len(game['guesses']) >= 6:
            del self.active_games[channel_id]
            await message.reply(file=file, content=f"Game over! The word was **{answer.upper()}**.")
        else:
            await message.reply(file=file)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.content.lower() == "new wordle":
            await self.new_wordle(message)
        elif message.content.lower() == "end wordle":
            await self.end_wordle(message)
        elif message.content.lower().startswith("guess "):
            await self.guess(message)

def setup(bot):
    bot.add_cog(Wordle(bot))
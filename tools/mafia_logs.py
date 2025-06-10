import nextcord
from nextcord.ext import commands
from cogs.transcript import create_channel_transcript
from datetime import datetime
import re

MAFIA_BOTS = [
    758999095070687284,
    511786918783090688,
]
GREEN_CHECK = "<:green_check2:1291173532432203816>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class MafiaLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mafia Logs cog loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel:
            return
        if not message.embeds:
            return
        if not message.channel.name == "mafia":
            return
        if not message.author.bot:
            return
        if not message.embeds[0].title:
            return
        if "Game Over" not in message.embeds[0].title:
            return
        if message.author.id not in MAFIA_BOTS:
            return
        
        members, duration = await self.get_mafia_game_info(message)
        transcript, messages = await create_channel_transcript(message.channel)
        embed = nextcord.Embed(title="Mafia Game Transcript", description=f"**Time Completed:** <t:{message.created_at.timestamp()}:f>\n**Server:** {message.guild.name}\n**Duration:** {duration}\n**Players:** {len(members)}")
        await self.send_transcript(transcript, embed, message)

    async def send_transcript(self, transcript, embed, message):
        configuration = configuration.find_one({"_id": "config"})
        mafia_logs_channel = configuration["mafia_logs"]
        if not mafia_logs_channel:
            return
        channel = mafia_logs_channel.get(str(message.guild.id))
        if not channel:
            return
        channel = self.bot.get_channel(int(channel))
        if not channel:
            return
        await channel.send(embed=embed, file=transcript)
        await message.add_reaction(GREEN_CHECK)

    async def get_mafia_game_info(self, message):
        members = []
        for field in message.embeds[0].fields:
            if field.name and field.value:
                mentions = re.findall(r'<@!?(\d+)>', field.value)
                members.extend(mentions)
        duration = message.channel.created_at - datetime.now()
        return members, duration
def setup(bot):
    bot.add_cog(MafiaLogs(bot))
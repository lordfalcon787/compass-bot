import nextcord
from nextcord.ext import commands
from cogs.transcript import create_channel_transcript
from datetime import datetime
import re
from utils.github_uploader import get_github_uploader

MAFIA_BOTS = [758999095070687284, 511786918783090688, 204255221017214977]
GREEN_CHECK = "<:green_check2:1291173532432203816>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class MafiaLogs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.github_uploader = get_github_uploader()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mafia Logs cog loaded")

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.channel:
            return
        if isinstance(message.channel, nextcord.DMChannel):
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
        print("Mafia game detected")
        transcript, messages = await create_channel_transcript(message.channel)
        members, duration = await self.get_mafia_game_info(message)
        timestamp = message.created_at.timestamp()
        timestamp_int = int(timestamp)
        
        # Upload transcript to GitHub
        file_url = None
        if self.github_uploader:
            try:
                # Get file content as bytes
                transcript.fp.seek(0)  # Reset file pointer
                file_content = transcript.fp.read()
                if isinstance(file_content, str):
                    file_content = file_content.encode('utf-8')
                
                file_url = await self.github_uploader.upload_transcript(
                    file_content, 
                    message.channel.name, 
                    message.created_at
                )
                print(f"Transcript uploaded to: {file_url}")
            except Exception as e:
                print(f"Failed to upload transcript to GitHub: {e}")
        
        embed = nextcord.Embed(
            title="Mafia Game Transcript", 
            description=f"**Time Completed:** <t:{timestamp_int}:f>\n**Server:** {message.guild.name}\n**Duration:** {duration}\n**Players:** {len(members)}\n**Message Count:** {len(messages)}"
        )
        embed.set_thumbnail(url=message.guild.icon.url)
        
        # Add GitHub link to embed if available
        if file_url:
            embed.add_field(name="📄 Transcript", value=f"[View Online]({file_url})", inline=False)
        
        await self.send_transcript(transcript, embed, message)
        
        # Store in MongoDB
        collection = db["Mafia Games"]
        doc_data = {
            "_id": message.channel.id,
            "timestamp": timestamp_int,
            "server": message.guild.name,
            "duration": duration,
            "players": len(members),
            "message_count": len(messages)
        }
        
        if file_url:
            doc_data["file_url"] = file_url
            
        collection.insert_one(doc_data)

    async def send_transcript(self, transcript, embed, message):
        config = configuration.find_one({"_id": "config"})
        mafia_logs_channel = config["mafia_logs"]
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
        duration = datetime.now(message.channel.created_at.tzinfo) - message.channel.created_at
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        duration = f"{minutes} minutes and {seconds} seconds"
        return members, duration

def setup(bot):
    bot.add_cog(MafiaLogs(bot))
import asyncio
import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
AUTO = [1267527896218468412, 1267530934723281009]

class Donosticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Donosticky cog loaded.")
        self.messages_task.start()

    @tasks.loop(hours=3)
    async def messages_task(self):
        await self.clean_old_messages()

    async def clean_old_messages(self):
        time_threshold = int(datetime.now().timestamp()) - 43200
        for channel_id in AUTO:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    print(f"Cleaning old messages from {channel.name}")
                    try:                        
                        try:
                            async with asyncio.timeout(900):
                                print("Getting messages")
                                messages = [msg async for msg in channel.history(limit=None) 
                                          if int(msg.edited_at.timestamp()) < time_threshold and not msg.pinned]
                        except asyncio.TimeoutError:
                            print("Timeout error")
                            messages = []
                        print(f"Found {len(messages)} messages to clean")
                        await self.check_old_messages(messages)
                        print(f"Cleaned {len(messages)} messages from {channel.name}")
                    except Exception as e:
                        print(f"Error cleaning {channel.name}: {str(e)}")
        print("Done cleaning messages")

    async def check_old_messages(self, messages):
        for message in messages:
            try:
                if message.author.id != self.bot.user.id:
                    pass
                elif not message.embeds:
                    pass
                elif not message.embeds[0].title:
                    pass
                if "completed" in message.embeds[0].title.lower() or "denied" in message.embeds[0].title.lower():
                    print(f"Deleting message {message.id} from {message.channel.name}")
                    await message.delete()
                    await asyncio.sleep(1)
            except Exception as e:
                print(f"Error checking message {message.id}: {str(e)}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in AUTO:
            return
        elif message.author.bot:
            return
        await message.delete(delay=1800)
                    
def setup(bot):
    bot.add_cog(Donosticky(bot))
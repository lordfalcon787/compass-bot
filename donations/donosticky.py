import asyncio
import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
AUTO = [1267527896218468412, 1267530934723281009]

class Donosticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        if self.messages_task.is_running():
            self.messages_task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Donosticky cog loaded.")
        if not self.messages_task.is_running():
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
                                messages = [msg async for msg in channel.history(limit=100) if msg.edited_at and msg.edited_at.timestamp() < time_threshold]
                        except asyncio.TimeoutError:
                            print("Timeout error")
                            messages = []
                        print(f"Found {len(messages)} messages to potentially clean")
                        if len(messages) > 0:
                            await self.check_old_messages(messages, channel)
                        else:
                            print(f"No messages to clean from {channel.name}")
                    except Exception as e:
                        print(f"Error cleaning {channel.name}: {str(e)}")
        print("Completed cleaning messages.")

    async def check_old_messages(self, messages, channel):
        cleaned = 0
        for message in messages:
            try:
                if message.author.id != self.bot.user.id:
                    continue
                elif not message.embeds:
                    continue
                elif not message.embeds[0].title:
                    continue
                elif "completed" in message.embeds[0].title.lower() or "denied" in message.embeds[0].title.lower():
                    print(f"Deleting message {message.id} from {message.channel.name}")
                    await message.delete()
                    cleaned += 1
                    await asyncio.sleep(5)
            except Exception as e:
                print(f"Error checking message {message.id}: {str(e)}")
        print(f"Cleaned {cleaned} messages from {channel.name}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in AUTO:
            return
        elif message.author.bot:
            return
        await message.delete(delay=1800)
                    
def setup(bot):
    bot.add_cog(Donosticky(bot))
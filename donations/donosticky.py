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
        time_threshold = datetime.now() - timedelta(hours=12)
        for channel_id in AUTO:
                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    try:                        
                        try:
                            async with asyncio.timeout(120):
                                messages = [msg async for msg in channel.history(limit=None) 
                                          if msg.created_at < time_threshold and not msg.pinned]
                        except asyncio.TimeoutError:
                            messages = []
                        await self.check_old_messages(messages)
                    except:
                        pass

    async def check_old_messages(self, messages):
        for message in messages:
            try:
                if message.author.id != self.bot.user.id:
                    pass
                elif not message.embeds:
                    pass
                elif not message.embeds[0].title:
                    pass
                if "completed" in message.embeds[0].title.lower():
                    await message.delete()
                    await asyncio.sleep(1)
            except:
                pass

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in AUTO:
            return
        elif message.author.bot:
            return
        await message.delete(delay=1800)
                    
def setup(bot):
    bot.add_cog(Donosticky(bot))
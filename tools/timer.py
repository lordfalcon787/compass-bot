import asyncio
import nextcord
from nextcord.ext import commands
from datetime import datetime

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Timer"]

collection.create_index("end_time")

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_timers = {}

    def cog_unload(self):
        for timer_id, task in self.active_timers.items():
            if not task.done():
                task.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Timer cog loaded.")
        await self.load_timers()

    async def load_timers(self):
        current_time = int(datetime.now().timestamp())
        timers = list(collection.find({}))
        
        for timer in timers:
            end_time = timer["end_time"]
            seconds_remaining = end_time - current_time
            
            if seconds_remaining <= 0:
                collection.delete_one({"_id": timer["_id"]})
                asyncio.create_task(self.timer_end(timer))
            else:
                self.schedule_timer(timer, seconds_remaining)

    def schedule_timer(self, timer, seconds_remaining):
        timer_id = timer["_id"]
        if timer_id in self.active_timers and not self.active_timers[timer_id].done():
            self.active_timers[timer_id].cancel()
        task = asyncio.create_task(self.wait_and_end_timer(timer, seconds_remaining))
        self.active_timers[timer_id] = task

    async def wait_and_end_timer(self, timer, seconds_remaining):
        try:
            await asyncio.sleep(seconds_remaining)
            collection.delete_one({"_id": timer["_id"]})
            await self.timer_end(timer)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            print(f"Error in timer task: {e}")
        finally:
            if timer["_id"] in self.active_timers:
                del self.active_timers[timer["_id"]]

    async def timer_end(self, timer):
        try:
            channel = self.bot.get_channel(timer["channel"])
            msg = await channel.fetch_message(timer["_id"])
            users = [user async for user in msg.reactions[0].users() if not user.bot]
            users = [user.mention for user in users]
            if msg:
                if len(users) > 0:
                    e = await msg.reply(f"{' '.join(users)}")
                    await e.delete()
                embed = msg.embeds[0]
                embed.set_footer(text="Timer has ended.")
                await msg.edit(embed=embed)
                button = nextcord.ui.Button(label="View Timer", url=f"https://discord.com/channels/{timer['guild']}/{timer['channel']}/{timer['_id']}", emoji="⏰")
                view = nextcord.ui.View()
                view.add_item(button)
                await channel.send(f"<@{timer['host']}> your timer has ended!", view=view)
        except:
            pass

    @commands.command(name="timer")
    async def timer(self, ctx):
        split = ctx.message.content.split(" ")
        time = split[1]
        total_seconds = 0
        import re
        pattern = r'(\d+)([dhms])'
        matches = re.findall(pattern, time)
        for value, unit in matches:
            value = int(value)
            if unit == 'd':
                total_seconds += value * 86400
            elif unit == 'h':
                total_seconds += value * 3600
            elif unit == 'm':
                total_seconds += value * 60
            elif unit == 's':
                total_seconds += value
        if total_seconds < 1:
            await ctx.reply("Invalid time entered.", mention_author=False)
            return
        current_time = int(datetime.now().timestamp())
        end_time = current_time + total_seconds
        end_time = int(end_time)
        message = "Timer"
        if len(split) > 2:
            message = " ".join(split[2:])
        color = ctx.author.color
        embed = nextcord.Embed(title=message, description=f"Timer will end <t:{end_time}:R>", color=color)
        msg = await ctx.send(embed=embed)
        await ctx.message.delete()
        await msg.add_reaction("🔔")
        
        timer_data = {
            "_id": msg.id, 
            "end_time": end_time, 
            "host": ctx.author.id, 
            "channel": ctx.channel.id, 
            "guild": ctx.guild.id
        }
        
        collection.insert_one(timer_data)
        self.schedule_timer(timer_data, total_seconds)

def setup(bot):
    bot.add_cog(Timer(bot))
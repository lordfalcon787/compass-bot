import asyncio
import nextcord
from nextcord.ext import commands, tasks
from datetime import datetime

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Timer"]

collection.create_index("end_time")

class Timer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        if self.check_timers.is_running():
            self.check_timers.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Timer cog loaded.")
        if not self.check_timers.is_running():
            self.check_timers.start()

    @tasks.loop(seconds=2)
    async def check_timers(self):
        current_time = int(datetime.now().timestamp())
        expired_timers = list(collection.find({"end_time": {"$lt": current_time}}).limit(100))
        
        for timer in expired_timers:
            collection.delete_one({"_id": timer["_id"]})
            asyncio.create_task(self.timer_end(timer))

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
        time = time.replace("d", "*86400+").replace("h", "*3600+").replace("m", "*60+").replace("s", "*1+")
        if time.endswith('+'):
            time = time[:-1]
        total_seconds = eval(time)
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
        collection.insert_one({"_id": msg.id, "end_time": end_time, "host": ctx.author.id, "channel": ctx.channel.id, "guild": ctx.guild.id})

def setup(bot):
    bot.add_cog(Timer(bot))
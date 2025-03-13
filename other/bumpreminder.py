import nextcord
import time
import datetime
from nextcord.ext import commands, tasks
from nextcord import SlashOption
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Bumps"]


class BumpReminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("BumpReminder cog loaded")
        self.bump_reminder.start()
        self.cache_update.start()

    @tasks.loop(minutes=5)
    async def cache_update(self):
        doc = collection.find_one({"_id": "data"})
        if doc:
            self.cache = doc

    @tasks.loop(minutes=1)
    async def bump_reminder(self):
        guilds = self.cache.get("guilds")
        pings = self.cache.get("pings")
        channels = self.cache.get("channels")
        for guild_id in guilds.keys():
            guild = self.bot.get_guild(int(guild_id))
            if guild:
                channel = guild.get_channel(int(guilds[guild_id]))
                if channel:
                    channel_time = channels[guild_id]
                    if channel_time:
                        current_time = int(datetime.datetime.now().timestamp())
                        if current_time - channel_time >= 7200:
                            try:
                                await channel.send(f"{pings[guild_id]} - It is time to bump the server, please bump by running </bump:947088344167366698>.")
                            except:
                                pass

    @nextcord.slash_command(name="setbumpchannel", description="Set the channel for bump reminders.")
    async def setbumpchannel(self, interaction: nextcord.Interaction, ping_role: nextcord.Role = SlashOption(description="The role to ping."), channel: nextcord.TextChannel = SlashOption(description="The channel to set the bump reminder in.")):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to set the bump reminder channel.", ephemeral=True)
            return
        collection.update_one({"_id": "data"}, {"$set": {f"guilds.{interaction.guild.id}": channel.id, f"pings.{interaction.guild.id}": ping_role.mention}}, upsert=True)
        await interaction.response.send_message(f"Bump reminder channel set to {channel.mention}", ephemeral=True)
        self.cache[f"{interaction.guild.id}"] = channel.id

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.id != 302050872383242240:
            return
        guild_id = str(message.guild.id)
        guilds = self.cache.get("guilds")
        if guild_id in guilds:
            channel_id = guilds[guild_id]
            if message.channel.id != channel_id:
                return
        else:
            return
        if not message.embeds:
            return
        if not message.embeds[0].description:
            return
        if "bump done" in message.embeds[0].description.lower():
            collection.update_one({"_id": "data"}, {"$set": {f"channels.{guild_id}": int(datetime.datetime.now().timestamp())}}, upsert=True)

def setup(bot: commands.Bot):
    bot.add_cog(BumpReminder(bot))
        


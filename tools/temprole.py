import nextcord
import asyncio
import re
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Temprole"]

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

class TempRole(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cache = []

    @commands.Cog.listener()
    async def on_ready(self):
        print("TempRole cog loaded")
        self.check_temprole.start()

    @tasks.loop(hours=1)
    async def check_temprole(self):
        one_hour_from_now = datetime.now() + timedelta(hours=1)
        cases = list(collection.find({"end_time": {"$lt": one_hour_from_now}}))
        for case in cases:
            asyncio.create_task(self.end_temprole(case))

    async def end_temprole(self, case):
        doc = collection.find_one({"_id": case["_id"]})
        if case["_id"] in self.cache:
            return
        self.cache.append(case["_id"])
        if not doc:
            return
        guild = self.bot.get_guild(doc["guild"])
        if not guild:
            return
        user = guild.get_member(doc["user"])
        role = guild.get_role(doc["role"])
        if not user:
            return
        if not role:
            return
        if role not in user.roles:
            return
        await user.remove_roles(role)
        collection.delete_one({"_id": case["_id"]})
        self.cache.remove(case["_id"])

    @commands.command(name="temprole")
    async def temprole(self, ctx):
        if not ctx.author.guild_permissions.manage_roles:
            await ctx.send("You do not have permission to use this command.")
            return
        split = ctx.message.content.split(" ")
        if len(split) < 2:
            await ctx.reply("Correct usage: `!temprole [user] [duration] [role]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        user = split[1]
        if user == "cancel":
            await self.temprole_cancel(ctx)
            return
        if len(split) < 3:
            await ctx.reply("Correct usage: `!temprole [user] [duration] [role]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        duration = split[2]
        if len(split) < 4:
            await ctx.reply("Correct usage: `!temprole [user] [duration] [role]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        role = split[3]
        try:
            user = ctx.guild.get_member(int(user))
        except ValueError:
            await ctx.reply("Invalid user ID.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if not user:
            await ctx.reply("Invalid user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if duration.isdigit() or "<@&" in duration:
            old_role = role
            role = duration
            duration = old_role
        try:
            role = ctx.guild.get_role(int(role))
        except ValueError:
            await ctx.reply("Invalid role ID.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if not role:
            await ctx.reply("Invalid role.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        duration = self.get_duration(duration)
        if duration < 1:
            await ctx.reply("Invalid duration.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        readable = self.get_readable_duration(duration)
        await user.add_roles(role)
        current_case = collection.find_one({"_id": "current_case"})
        if not current_case:
            current_case = 0
        current_case += 1
        collection.update_one({"_id": "current_case"}, {"$set": {"current_case": current_case}}, upsert=True)
        collection.insert_one({"_id": current_case, "user": user.id, "role": role.id, "guild": ctx.guild.id, "duration": duration, "end_time": datetime.now() + timedelta(seconds=duration)})
        embed = nextcord.Embed(title=f"Temporary Role Case #{current_case}", description=f"Added temporary role {role.name} to {user.mention} for {readable}, it will be removed in <t:{int((datetime.now() + timedelta(seconds=duration)).timestamp())}:R>.", color=nextcord.Color.blurple())
        await ctx.reply(embed=embed, mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    async def temprole_cancel(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) < 3:
            await ctx.reply("Correct usage: `!temprole cancel [case number]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        case = split[2]
        if not case.isdigit():
            await ctx.reply("Invalid case.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        case = collection.find_one({"_id": int(case)})
        if not case:
            await ctx.reply("Invalid case.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if case["end_time"] < datetime.now():
            await ctx.reply("This case has already expired.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        collection.delete_one({"_id": case["_id"]})
        await ctx.reply("Case cancelled.", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @nextcord.slash_command(name="temprole", description="Temporary role command")
    async def temprole_slash(self, interaction: nextcord.Interaction):
        pass

    @temprole_slash.subcommand(name="cancel", description="Cancel a temporary role removal")
    async def temprole_slash_cancel(self, interaction: nextcord.Interaction, case: int):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        case = collection.find_one({"_id": case})
        if not case:
            await interaction.response.send_message("Invalid case.", ephemeral=False)
            return
        if case["end_time"] < datetime.now():
            await interaction.response.send_message("This case has already expired.", ephemeral=False)
            return
        collection.delete_one({"_id": case["_id"]})
        await interaction.response.send_message("Case cancelled.", ephemeral=False)

    @temprole_slash.subcommand(name="add", description="Add a temporary role to a user")
    async def temprole_slash_add(self, interaction: nextcord.Interaction, user: nextcord.Member, duration: str, role: nextcord.Role):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        duration = self.get_duration(duration)
        if duration < 1:
            await interaction.response.send_message("Invalid duration.", ephemeral=True)
            return
        readable = self.get_readable_duration(duration)
        await user.add_roles(role)
        current_case = collection.find_one({"_id": "current_case"})
        if not current_case:
            current_case = 0
        current_case += 1
        collection.update_one({"_id": "current_case"}, {"$set": {"current_case": current_case}}, upsert=True)
        collection.insert_one({"_id": current_case, "user": user.id, "role": role.id, "guild": interaction.guild.id, "duration": duration, "end_time": datetime.now() + timedelta(seconds=duration)})
        embed = nextcord.Embed(title=f"Temporary Role Case #{current_case}", description=f"Added temporary role {role.name} to {user.mention} for {readable}, it will be removed in <t:{int((datetime.now() + timedelta(seconds=duration)).timestamp())}:R>.", color=nextcord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    def get_duration(self, duration: str):
        time = duration.lower()
        total_seconds = 0
        
        # Extract time units safely using regex
        pattern = r'(\d+)([dhms])'
        matches = re.findall(pattern, time)
        
        if not matches:
            # If no matches found, try to parse as plain number (assume seconds)
            try:
                total_seconds = int(duration)
            except ValueError:
                return 0
        else:
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
        
        return total_seconds
    
    def get_readable_duration(self, duration: int):
        days = duration // 86400
        hours = (duration % 86400) // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60
        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds:
            parts.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        return " ".join(parts) if parts else "0 seconds"

def setup(bot):
    bot.add_cog(TempRole(bot))
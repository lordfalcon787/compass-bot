import nextcord
import asyncio
import re
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta
from utils.mongo_connection import MongoConnection
from difflib import SequenceMatcher

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

    def extract_user_id(self, user_text):
        match = re.match(r'<@!?(\d+)>', user_text)
        if match:
            return int(match.group(1))
        try:
            return int(user_text)
        except ValueError:
            return None

    def find_best_role_match(self, guild, role_name):
        role_name = role_name.lower()
        best_match = None
        best_ratio = 0
        
        for role in guild.roles:
            if role.name == "@everyone":
                continue
            if role.name.lower() == role_name:
                return role
            if role_name in role.name.lower():
                return role
            ratio = SequenceMatcher(None, role_name, role.name.lower()).ratio()
            if ratio > best_ratio and ratio > 0.6:
                best_ratio = ratio
                best_match = role
        
        return best_match

    def parse_command_parts(self, message_content):
        parts = message_content.split()
        
        if len(parts) < 3:
            return None, None, None
        
        user_part = parts[1]
        
        duration_pattern = r'\d+[dhms]'
        duration_part = None
        role_parts = []
        
        for i in range(len(parts) - 1, 1, -1):
            if re.match(duration_pattern, parts[i]):
                duration_part = parts[i]
                role_parts = parts[2:i]
                break
        
        if duration_part is None:
            duration_part = parts[-1]
            role_parts = parts[2:-1]
        
        role_name = " ".join(role_parts) if role_parts else ""
        
        return user_part, role_name, duration_part

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
        seconds_to_wait = (doc["end_time"] - datetime.now()).total_seconds()
        if seconds_to_wait > 0:
            await asyncio.sleep(seconds_to_wait)
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
        if len(split) >= 2 and split[1] == "cancel":
            await self.temprole_cancel(ctx)
            return
        
        user_part, role_name, duration_part = self.parse_command_parts(ctx.message.content)
        
        if not user_part or not role_name or not duration_part:
            await ctx.reply("Correct usage: `!temprole [user] [role name] [duration]`\nExample: `!temprole @user Member of the Month 30d`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        user_id = self.extract_user_id(user_part)
        if not user_id:
            await ctx.reply("Invalid user. Please mention a user or provide a valid user ID.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        user = ctx.guild.get_member(user_id)
        if not user:
            await ctx.reply("User not found in this server.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        role = self.find_best_role_match(ctx.guild, role_name)
        if not role:
            await ctx.reply(f"Could not find a role matching '{role_name}'. Please check the role name.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        duration = self.get_duration(duration_part)
        if duration < 1:
            await ctx.reply("Invalid duration. Use formats like: 30d, 12h, 45m, 60s", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        if role in user.roles:
            await ctx.reply(f"{user.mention} already has the {role.name} role.", mention_author=False)
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
        
        embed = nextcord.Embed(
            title=f"Temporary Role Case #{current_case}", 
            description=f"Added temporary role **{role.name}** to {user.mention} for **{readable}**.", 
            color=nextcord.Color.blurple()
        )
        await ctx.reply(embed=embed, mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        
        if duration < 3600:
            asyncio.create_task(self.end_temprole(current_case))

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
        embed = nextcord.Embed(title=f"Temporary Role Case #{current_case}", description=f"Added temporary role {role.name} to {user.mention} for {readable}.", color=nextcord.Color.blurple())
        await interaction.response.send_message(embed=embed, ephemeral=False)
    
    def get_duration(self, duration: str):
        time = duration.lower()
        total_seconds = 0
        
        pattern = r'(\d+)([dhms])'
        matches = re.findall(pattern, time)
        
        if not matches:
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
import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]
collection = db["Moderation"]

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Moderation cog loaded.")

    @commands.command(name="warn")
    async def warn_cmd(self, ctx, member: nextcord.Member, *, reason: str):
        return
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["warn"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            return

    @commands.command(name="timeout")
    async def timeout_cmd(self, ctx, member: nextcord.Member, time: str, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["timeout"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot timeout this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        time_to_timeout = time.lower()
        time_to_timeout = await self.get_time_until_timeout(time_to_timeout)
            
        if time_to_timeout <= 0:
            await ctx.reply("Invalid time format. Please use a format like 1d, 3h, 30m, etc.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
            
        timeout_until = datetime.now() + timedelta(seconds=time_to_timeout)
        
        try:
            await member.timeout(timeout_until, reason=reason)
            await ctx.message.add_reaction(GREEN_CHECK)
            await ctx.reply(f"Timed out **{member.name}** for {time_to_timeout} with reason: {reason}", mention_author=False)
            doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
            if not doc:
                doc = 0
            else:
                doc = doc.get("current_case")
            doc += 1
            collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "timeout", "date": timeout_until.strftime("%d/%m/%Y")}}}, upsert=True)
            
            if logs:
                embed = nextcord.Embed(title="Member Timeout", description=f"User Timed out: **{member.name}** ({member.id})\nTimed out by: **{ctx.author.name}** ({ctx.author.id})\nDuration: {time_to_timeout}\nReason: {reason}")
                try:
                    logs = self.bot.get_channel(int(logs))
                    await logs.send(embed=embed)
                except:
                    pass
        except:
            await ctx.reply("I was unable to timeout the user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)

    
    @commands.command(name="kick")
    async def kick_cmd(self, ctx, member: nextcord.Member, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["kick"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.kick_members:
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot kick this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.send(f"You have been kicked from **{ctx.guild.name}** for reason: {reason}")
        except:
            pass
        try:
            await member.kick(reason=reason)
        except:
            await ctx.reply("I was unable to kick the user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Kicked **{member.name}** for reason: {reason}", mention_author=False)
        doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "kick", "date": datetime.now().strftime("%d/%m/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title="Member Kick", description=f"User Kicked: **{member.name}** ({member.id})\nKicked by: **{ctx.author.name}** ({ctx.author.id})\nReason: {reason}")
            try:
                await logs.send(embed=embed)
            except:
                pass

    @commands.command(name="ban")
    async def ban_cmd(self, ctx, member: nextcord.User, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["ban"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.ban_members:
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot ban this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.send(f"You have been banned from **{ctx.guild.name}** for reason: {reason}")
        except:
            pass
        try:
            await member.ban(reason=reason)
        except:
            await ctx.reply("I was unable to ban the user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Banned **{member.name}** for reason: {reason}", mention_author=False)
        doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "ban", "date": datetime.now().strftime("%d/%m/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title="Member Ban", description=f"User Banned: **{member.name}** ({member.id})\nBanned by: **{ctx.author.name}** ({ctx.author.id})\nReason: {reason}")
            try:
                await logs.send(embed=embed)
            except:
                pass

    @commands.command(name="unban")
    async def unban_cmd(self, ctx, member: nextcord.User, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["ban"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.ban_members:
            return  
        try:
            await ctx.guild.unban(member)
        except:
            await ctx.reply("I was unable to unban the user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Unbanned **{member.name}** for reason: {reason}", mention_author=False)
        doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "unban", "date": datetime.now().strftime("%d/%m/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title="Member Unban", description=f"User Unbanned: **{member.name}** ({member.id})\nUnbanned by: **{ctx.author.name}** ({ctx.author.id})\nReason: {reason}")
            try:
                await logs.send(embed=embed)
            except:
                pass
        try:
            await member.send(f"You have been unbanned from **{ctx.guild.name}** for reason: {reason}")
        except:
            pass

    @commands.command(name="removetimeout", aliases=["untimeout", "rto"])
    async def removetimeout_cmd(self, ctx, member: nextcord.Member, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["timeout"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.moderate_members:
            return
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot modify the timeout of this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if not member.communication_disabled_until or member.communication_disabled_until <= datetime.now():
            await ctx.reply("This user is not timed out.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.remove_timeout()
        except:
            await ctx.reply("I was unable to remove the timeout.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Removed the timeout from **{member.name}**, for reason: {reason}", mention_author=False)
        doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "untimeout", "date": datetime.now().strftime("%d/%m/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title="Member Timeout Removed", description=f"User Timed Out: **{member.name}** ({member.id})\nTimed Out by: **{ctx.author.name}** ({ctx.author.id})")
            try:
                await logs.send(embed=embed)
            except:
                pass
    
    @commands.command(name="removewarn", aliases=["rwarn", "deletewarn", "delwarn"])
    async def removewarn_cmd(self, ctx, member: nextcord.Member, amount: int):
        return
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["warn"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            return
        
    @nextcord.slash_command(name="quarantine", description="Quarantine a user")
    async def quarantine(self, interaction: nextcord.Interaction):
        pass

    @quarantine.subcommand(name="add", description="Quarantine a user.")
    async def add(self, interaction: nextcord.Interaction, member: nextcord.Member):
        await interaction.response.send_message(f"Quarantined **{member.name}**.", ephemeral=True)

    @quarantine.subcommand(name="configure", description="Configure the quarantine system.")
    async def configure(self, interaction: nextcord.Interaction):
        await interaction.response.send_message(f"Quarantine configured.", ephemeral=True)

    @quarantine.subcommand(name="remove", description="Remove a user from quarantine.")
    async def remove(self, interaction: nextcord.Interaction, member: nextcord.Member):
        await interaction.response.send_message(f"Removed **{member.name}** from quarantine.", ephemeral=True)

    async def get_time_until_timeout(self, time: str):
        time_units = {
            's': 1,           
            'm': 60,           
            'h': 3600,        
            'd': 86400,       
            'w': 604800      
        } 
        seconds = 0
        current_num = ""
        for char in time:
            if char.isdigit():
                current_num += char
            elif char in time_units:
                if current_num:
                    seconds += int(current_num) * time_units[char]
                    current_num = ""
        if current_num:
            seconds += int(current_num)
        return seconds

def setup(bot):
    bot.add_cog(Moderation(bot))
        

        
    
    

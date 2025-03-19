import nextcord
from nextcord.ext import commands
from datetime import datetime, timedelta, timezone
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
    async def warn_cmd(self, ctx, member: nextcord.Member, *, reason: str = "No reason provided"):
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
        if member.top_role >= ctx.author.top_role:
            await ctx.reply("You cannot warn this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        await member.send(f"You have been warned in **{ctx.guild.name}** for reason: {reason}")
        await ctx.reply(f"Warned **{member.name}** for reason: {reason}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        collection.update_one({"_id": f"warn_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "warn", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title=f"Member Warn | Case #{doc}", description=f"**User Warned:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass

    @commands.command(name="timeout", aliases=["mute", "to"])
    async def timeout_cmd(self, ctx, member: nextcord.Member, time: str, *, reason: str = "No reason provided"):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["timeout"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        bot_member = ctx.guild.get_member(self.bot.user.id)
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            return
        if member.top_role >= ctx.author.top_role or member.top_role >= bot_member.top_role:
            await ctx.reply("You cannot timeout this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        time_to_timeout = time.lower()
        time_to_timeout, readable = await self.get_time_until_timeout(time_to_timeout)
            
        if time_to_timeout <= 0:
            await ctx.reply("Invalid time format. Please use a format like 1d, 3h, 30m, etc.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
            
        timeout_until = datetime.now() + timedelta(seconds=time_to_timeout)
        
        try:
            await member.timeout(timeout_until, reason=reason)
            await ctx.message.add_reaction(GREEN_CHECK)
            await ctx.reply(f"Timed out **{member.name}** for {readable} with reason: {reason}", mention_author=False)
            doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
            if not doc:
                doc = 0
            else:
                doc = doc.get("current_case")
            doc += 1
            collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "timeout", "date": timeout_until.strftime("%m/%d/%Y")}}}, upsert=True)
            
            if logs:
                embed = nextcord.Embed(title=f"Member Timeout | Case #{doc}", description=f"**User Timed Out:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Duration:** {readable}\n**Reason:** {reason}", color=nextcord.Color.blurple())
                embed.set_footer(text=f"ID: {member.id}")
                embed.timestamp = datetime.now()
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
        bot_member = ctx.guild.get_member(self.bot.user.id)
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.kick_members:
            return
        if member.top_role >= ctx.author.top_role or member.top_role >= bot_member.top_role:
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
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "kick", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title=f"Member Kick | Case #{doc}", description=f"**User Kicked:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
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
        bot_member = ctx.guild.get_member(self.bot.user.id)
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.ban_members:
            return
        if member.top_role >= ctx.author.top_role or member.top_role >= bot_member.top_role:
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
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "ban", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title=f"Member Ban | Case #{doc}", description=f"**User Banned:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
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
        banned_users = await ctx.guild.bans()
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.ban_members:
            return
        if member not in banned_users:
            await ctx.reply("This user is not banned.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await ctx.guild.unban(member)
        except nextcord.Forbidden:
            await ctx.reply("I do not have permission to unban this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "unban", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title=f"Member Unban | Case #{doc}", description=f"**User Unbanned:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
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
        bot_member = ctx.guild.get_member(self.bot.user.id)
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.moderate_members:
            return
        if member.top_role >= ctx.author.top_role or member.top_role >= bot_member.top_role:
            await ctx.reply("You cannot modify the timeout of this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if not member.communication_disabled_until or member.communication_disabled_until <= datetime.now(timezone.utc):
            await ctx.reply("This user is not timed out.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.timeout(None, reason=reason)
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
        collection.update_one({"_id": f"mod_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "untimeout", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        if logs:
            embed = nextcord.Embed(title=f"Member Timeout Removed | Case #{doc}", description=f"**User Timed Out:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass

    @commands.command(name="clearwarns", aliases=["clearwarnings", "clw"])
    async def clearwarns_cmd(self, ctx, member: nextcord.Member, *, reason: str = "No reason provided"):
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["warn"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not ctx.author.guild_permissions.administrator:
            return
            
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        if not doc:
            await ctx.reply("No warns found for this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
            
        doc.pop("_id")
        doc.pop("current_case")
        num = 0
        warns_to_remove = []
        
        for case, data in doc.items():
            if int(data.get("member", 0)) == member.id:
                num += 1
                warns_to_remove.append(case)
                
        if num == 0:
            await ctx.reply("No warns found for this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        update_dict = {case: "" for case in warns_to_remove}
        collection.update_one(
            {"_id": f"warn_logs_{ctx.guild.id}"}, 
            {"$unset": update_dict}
        )
            
        await ctx.reply(f"Cleared {num} warns for **{member.name}**.", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        
        if logs:
            embed = nextcord.Embed(
                title=f"Member Warns Cleared", 
                description=f"**User Warned:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", 
                color=nextcord.Color.blurple()
            )
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass
    
    @commands.command(name="removewarn", aliases=["rwarn", "deletewarn", "delwarn"])
    async def removewarn_cmd(self, ctx, member: nextcord.Member, warn_id: str = None, *, reason: str = "No reason provided"):
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["warn"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not ctx.author.guild_permissions.administrator:
            return
        if not warn_id:
            await ctx.reply("Please provide a valid warn ID.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        if not doc:
            await ctx.reply("No warns found for this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if warn_id not in doc:
            await ctx.reply("Invalid warn ID.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        doc = doc.get(str(warn_id))
        await ctx.reply(f"Removed warn **{warn_id}** from **{member.name}** for reason: {reason}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        collection.update_one({"_id": f"warn_logs_{ctx.guild.id}"}, {"$unset": {str(warn_id): 1}})
        if logs:
            embed = nextcord.Embed(title=f"Member Warn Removed | Warn ID #{warn_id}", description=f"**User Warned:** {member.name} ({member.id})\n**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.set_footer(text=f"ID: {member.id}")
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass
        
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
            's': ('seconds', 1),           
            'm': ('minutes', 60),           
            'h': ('hours', 3600),        
            'd': ('days', 86400),       
            'w': ('weeks', 604800)      
        } 
        seconds = 0
        current_num = ""
        last_unit = None
        
        for char in time:
            if char.isdigit():
                current_num += char
            elif char in time_units:
                if current_num:
                    amount = int(current_num)
                    seconds += amount * time_units[char][1]
                    last_unit = (amount, time_units[char][0])
                    current_num = ""
                    
        if current_num:
            seconds += int(current_num)

        if last_unit:
            amount, unit = last_unit
            if amount == 1:
                unit = unit[:-1]
            readable = f"{amount} {unit}"
        else:
            readable = f"{seconds} seconds"
            
        return seconds, readable

def setup(bot):
    bot.add_cog(Moderation(bot))

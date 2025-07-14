import nextcord

from typing import Optional
from nextcord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]
collection = db["Moderation"]
modcredits = db["Mod Credits"]

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
LOADING = "<a:loading_animation:1218134049780928584>"

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Moderation cog loaded.")
        if self.check_ebl.is_running():
            pass
        else:
            await self.check_ebl.start()

    @tasks.loop(minutes=3)
    async def check_ebl(self):
        try:
            doc = collection.find_one({"_id": f"ebl_1205270486230110330"})
            if not doc:
                return
            guild = self.bot.get_guild(1205270486230110330)
            ebl_role = guild.get_role(1205270486359998556)
            if not ebl_role:
                return
            doc.pop("_id")
            for key, item in doc.items():
                if item.get("end") < datetime.now():
                    member = guild.get_member(int(key))
                    if member:
                        roles = item.get("roles", [])
                        member_roles = member.roles
                        try:
                            member_roles.remove(ebl_role)
                        except:
                            pass
                        for role in roles:
                            role_object = guild.get_role(int(role))
                            if role_object and role_object not in member_roles:
                                member_roles.append(role_object)
                        await member.edit(roles=member_roles)
                        collection.update_one({"_id": f"ebl_1205270486230110330"}, {"$unset": {str(member.id): ""}})
        except Exception as e:
            print(f"Error in check_ebl: {e}")
            return
        
    @commands.command(name="mcredit")
    async def mcredits_cmd(self, ctx):
        if ctx.guild.id != 1205270486230110330:
            return
        split = ctx.message.content.split(" ")
        if len(split) < 2:
            await self.mcredit_score(ctx, ctx.author)
            return
        second_arg = split[1]
        args = ["add", "remove", "lb", "leaderboard", "reset", "alltime", "total"]
        if not any(arg in second_arg for arg in args):
            second_arg = second_arg.replace("<@", "").replace(">", "")
            user = ctx.guild.get_member(int(second_arg))
            if not user:
                await ctx.reply("That user is not in the server.", mention_author=False)
                await ctx.message.add_reaction(RED_X)
                return
            await self.mcredit_score(ctx, user)
            return
        if second_arg == "lb" or second_arg == "leaderboard":
            await self.mcredit_leaderboard(ctx)
            return
        if second_arg == "reset":
            await self.mcredit_reset(ctx)
            return
        if second_arg == "add":
            await self.mcredit_add(ctx, split)
            return
        if second_arg == "remove":
            await self.mcredit_remove(ctx, split)
            return
        if second_arg == "alltime" or second_arg == "total":
            await self.mcredit_alltime(ctx)
            return
        
    async def mcredit_score(self, ctx, member):
        doc = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}"})
        if not doc:
            return
        doc = doc.get(str(member.id))
        embed = nextcord.Embed(title="Moderation Credit Report", color=nextcord.Color.blurple())
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed.set_thumbnail(url=member.display_avatar.url)
        try:
            points = doc.get("points", 0)
        except:
            points = 0
        try:
            warns = doc.get("warns", 0)
        except:
            warns = 0
        try:
            timeouts = doc.get("timeouts", 0)
        except:
            timeouts = 0
        try:
            kicks = doc.get("kicks", 0)
        except:
            kicks = 0
        try:
            bans = doc.get("bans", 0)
        except:
            bans = 0
        try:
            unbans = doc.get("unbans", 0)
        except:
            unbans = 0
        try:
            untimeouts = doc.get("untimeouts", 0)
        except:
            untimeouts = 0
        try:
            bonus = doc.get("bonus", 0)
        except:
            bonus = 0
        action_parts = []
        if warns > 0:
            action_parts.append(f"{warns} Warn{'s' if warns != 1 else ''}")
        if timeouts > 0:
            action_parts.append(f"{timeouts} Timeout{'s' if timeouts != 1 else ''}")
        if bans > 0:
            action_parts.append(f"{bans} Ban{'s' if bans != 1 else ''}")
        if kicks > 0:
            action_parts.append(f"{kicks} Kick{'s' if kicks != 1 else ''}")
        if unbans > 0:
            action_parts.append(f"{unbans} Unban{'s' if unbans != 1 else ''}")
        if untimeouts > 0:
            action_parts.append(f"{untimeouts} Un{'s' if untimeouts != 1 else ''}timeout")
        if bonus > 0:
            action_parts.append(f"{bonus} Bonus{'s' if bonus != 1 else ''}")
        actions = " / ".join(action_parts)
        if actions == "":
            actions = "None"
        position = "None"
        if points > 0:
            all_docs = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}"})
            if all_docs:
                points_list = []
                for m_id, m_data in all_docs.items():
                    if isinstance(m_data, dict) and m_id != "_id":
                        points_list.append((int(m_id), m_data.get("points", 0)))
                points_list.sort(key=lambda x: x[1], reverse=True)
                for idx, (m_id, pts) in enumerate(points_list, start=1):
                    if m_id == member.id:
                        position = idx
                        break
        embed.description = f"**Target:** {member.mention}\n**Position:** {position}\n**Points:** {points}\n**Actions:** {actions}"
        await ctx.reply(embed=embed, mention_author=False)

    async def mcredit_leaderboard(self, ctx):
        doc = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}"})
        if not doc:
            return
        points = {}
        for m_id, m_data in doc.items():
            if isinstance(m_data, dict):
                points[m_id] = m_data.get("points", 0)
        points_list = sorted(points.items(), key=lambda x: x[1], reverse=True)
        embed = nextcord.Embed(title="Moderation Credit Leaderboard", color=nextcord.Color.blurple())
        descp = ""
        embed.set_footer(text=f"Requested by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        for idx, (m_id, pts) in enumerate(points_list, start=1):
            member = ctx.guild.get_member(int(m_id))
            if member:
                descp += f"{idx}. {member.mention} - {pts} Points\n"
        embed.description = descp
        await ctx.reply(embed=embed, mention_author=False)

    async def mcredit_reset(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            return
        old_doc = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}"})
        alltime_doc = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}_alltime"})
        if alltime_doc:
            for m_id, m_data in old_doc.items():
                if m_id == "_id":
                    continue
                if isinstance(m_data, dict):
                    prev = alltime_doc.get(m_id, {})
                    prev_points = prev.get("points", 0)
                    new_points = m_data.get("points", 0) + prev_points
                    modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}_alltime"}, {"$set": {f"{m_id}.points": new_points}}, upsert=True)
        else:
            for m_id, m_data in old_doc.items():
                if m_id == "_id":
                    continue
                if isinstance(m_data, dict):
                    modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}_alltime"}, {"$set": {f"{m_id}.points": m_data.get("points", 0)}}, upsert=True)
        modcredits.delete_one({"_id": f"mod_credits_{ctx.guild.id}"})
        modcredits.insert_one({"_id": f"mod_credits_{ctx.guild.id}"})
        await ctx.message.add_reaction(GREEN_CHECK)

    async def mcredit_alltime(self, ctx):
        alltime_doc = modcredits.find_one({"_id": f"mod_credits_{ctx.guild.id}_alltime"})
        embed = nextcord.Embed(title="Moderation Credit All-Time Leaderboard", color=nextcord.Color.blurple())
        descp = ""
        for idx, (m_id, m_data) in enumerate(alltime_doc.items(), start=0):
            if m_id == "_id":
                continue
            if isinstance(m_data, dict):
                member = ctx.guild.get_member(int(m_id))
                if member:
                    descp += f"{idx}. {member.mention} - {m_data.get('points', 0)} Points\n"
        embed.description = descp
        await ctx.reply(embed=embed, mention_author=False)

    async def mcredit_add(self, ctx, split):
        if not ctx.author.guild_permissions.administrator:
            return
        if len(split) < 4:
            await ctx.reply("Correct usage: `!mcredit add [member] [amount]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        member = split[2]
        member = member.replace("<@", "").replace(">", "")
        amount = split[3]
        member = ctx.guild.get_member(int(member))
        if not member:
            await ctx.reply("That user is not in the server.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            amount = int(amount)
        except:
            await ctx.reply("Invalid amount.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{member.id}.points": amount, f"{member.id}.bonus": amount}}, upsert=True)
        await ctx.reply(f"Added `{amount}` points to **{member.name}**", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    async def mcredit_remove(self, ctx, split):
        if not ctx.author.guild_permissions.administrator:
            return
        if len(split) < 4:
            await ctx.reply("Correct usage: `!mcredit remove [member] [amount]`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        member = split[2]
        member = member.replace("<@", "").replace(">", "")
        amount = split[3]
        member = ctx.guild.get_member(int(member))
        if not member:
            await ctx.reply("That user is not in the server.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            amount = int(amount)
        except:
            await ctx.reply("Invalid amount.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{member.id}.points": -amount, f"{member.id}.bonus": -amount}}, upsert=True)
        await ctx.reply(f"Removed `{amount}` points from **{member.name}**", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
    
    @commands.command(name="nd")
    async def nd_cmd(self, ctx, member: nextcord.Member = None):
        if ctx.guild.id != 1205270486230110330:
            return
        author_roles = [role.id for role in ctx.author.roles]
        if 1209039929372315670 not in author_roles:
            await ctx.reply("You do not have permission to use this command.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member is None:
            await ctx.reply("Correct usage: `!nd @member`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        role = ctx.guild.get_role(1264605728195350620)
        if role not in member.roles:
            await member.add_roles(role)
            await ctx.reply(f"Added `No Drops` role to **{member.name}**", mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)
        else:
            await member.remove_roles(role)
            await ctx.reply(f"Removed `No Drops` role from **{member.name}**", mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="warn")
    async def warn_cmd(self, ctx, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!warn @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        user_roles = [role.id for role in ctx.author.roles]
        event_warn_var = ["event", "maf", "wordle", "gartic", "item guess", "rumbl", "bingo", "hangr", "rollkill", "roll kill", "cheat", "blacktea", "greentea", "redtea", "yellowtea", "mixtea", "black tea", "green tea", "red tea", "yellow tea", "mix tea", "split or steal", "sos", "gti", "guess the item", "battle", "bloony", "gaws", "giveaway", "mudae", "host", "game"]
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
        try:
            await member.send(f"You have been warned in **{ctx.guild.name}** for reason: {reason}")
        except:
            pass
        await ctx.reply(f"Warned **{member.name}** for reason: {reason}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        if not doc:
            doc = 0
        else:
            doc = doc.get("current_case")
        doc += 1
        if any(word in reason.lower() for word in event_warn_var):
            reason = f"[Event Warn] {reason}"
        collection.update_one({"_id": f"warn_logs_{ctx.guild.id}"}, {"$set": {"current_case": doc, f"{doc}": {"member": member.id, "reason": reason, "moderator": ctx.author.id, "type": "warn", "date": datetime.now().strftime("%m/%d/%Y")}}}, upsert=True)
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.warns": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def timeout_cmd(self, ctx, member: nextcord.Member = None, time: str = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!timeout @member time reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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
            modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.timeouts": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def kick_cmd(self, ctx, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!kick @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.kicks": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def ban_cmd(self, ctx, member: nextcord.User = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!ban @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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
        member_in_guild = ctx.guild.get_member(member.id)
        if member_in_guild:
            if member_in_guild.top_role >= ctx.author.top_role or member_in_guild.top_role >= bot_member.top_role:
                await ctx.reply("You cannot ban this user.", mention_author=False)
                await ctx.message.add_reaction(RED_X)
                return
            try:
                await member.send(f"You have been banned from **{ctx.guild.name}** for reason: {reason}")
            except:
                pass
        try:
            await ctx.guild.ban(member, reason=reason, delete_message_seconds=0)
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
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.bans": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def unban_cmd(self, ctx, member: nextcord.User = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!unban @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        logs = config["logs"]
        config = config["ban"]
        logs = logs.get(str(ctx.guild.id))
        config = config.get(str(ctx.guild.id))
        banned_users = []
        async for ban in ctx.guild.bans():
            banned_users.append(ban.user)
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
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.unbans": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def removetimeout_cmd(self, ctx, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!removetimeout @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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
        modcredits.update_one({"_id": f"mod_credits_{ctx.guild.id}"}, {"$inc": {f"{ctx.author.id}.untimeouts": 1, f"{ctx.author.id}.points": 1}}, upsert=True)
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
    async def clearwarns_cmd(self, ctx, member: nextcord.Member = None, *, reason: str = "No reason provided"):
        if member is None:
            await ctx.reply("Correct usage: `!clearwarns @member reason`", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
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

    @commands.command(name="modlogs", aliases=["modlog", "moderationlogs", "moderationlog"])
    async def modlogs_cmd(self, ctx, member: nextcord.Member = None):
        if not ctx.author.guild_permissions.manage_messages:
            return
        if not member:
            member = ctx.author
            
        doc = collection.find_one({"_id": f"mod_logs_{ctx.guild.id}"})
        if not doc:
            await ctx.reply("No moderation logs found for this guild.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
            
        total_cases = doc.get("current_case", 0)
        doc.pop("_id")
        doc.pop("current_case")
        all_cases = []
        
        for case_num in range(total_cases, 0, -1):
            case = doc.get(str(case_num))
            if not case:
                continue
                
            if case.get("member") != member.id:
                continue
                
            try:
                date = datetime.strptime(case.get("date", ""), "%m/%d/%Y")
                formatted_date = date.strftime("%m/%d/%Y")
            except:
                formatted_date = "Unknown date"
                
            action_type = case.get("type", "unknown")
            mod_id = case.get("moderator")
            moderator = ctx.guild.get_member(mod_id)
            mod_name = moderator.name if moderator else str(mod_id)
            reason = case.get("reason", "no reason given")
            
            entry = {
                "case_num": case_num,
                "action_type": action_type,
                "date": formatted_date,
                "mod_name": mod_name,
                "reason": reason
            }
            
            all_cases.append(entry)
            
        if not all_cases:
            await ctx.reply("No moderation logs found for this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
            
        page_size = 10
        total_pages = (len(all_cases) + page_size - 1) // page_size
        current_page = 0
        
        def create_embed(page):
            description = ""
            start = page * page_size
            end = min(start + page_size, len(all_cases))
            
            for i in range(start, end):
                case = all_cases[i]
                entry = (
                    f"**#{case['case_num']} | {case['action_type']} | {case['date']}**\n"
                    f"**Moderator:** {case['mod_name']}\n"
                    f"**Reason:** {case['reason']}\n\n"
                )
                description += entry
                
            embed = nextcord.Embed(
                title="Mod logs",
                description=description,
                color=0x2F3136
            )
            
            footer_text = f"Page {page + 1}/{total_pages} • {len(all_cases)} cases shown"
            embed.set_footer(text=footer_text)
            if member:
                embed.set_author(name=f"Logs for {member.name}", icon_url=member.display_avatar.url)
            return embed
        
        embed = create_embed(current_page)
        
        if total_pages > 1:
            view = nextcord.ui.View()
            
            prev_button = nextcord.ui.Button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.gray)
            next_button = nextcord.ui.Button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.gray)
            
            prev_button.disabled = True
            
            async def previous_callback(interaction):
                nonlocal current_page
                if interaction.user != ctx.author:
                    return
                current_page = max(0, current_page - 1)
                prev_button.disabled = current_page == 0
                next_button.disabled = current_page == total_pages - 1
                await interaction.message.edit(embed=create_embed(current_page), view=view)
                
            async def next_callback(interaction):
                nonlocal current_page
                if interaction.user != ctx.author:
                    return
                current_page = min(total_pages - 1, current_page + 1)
                prev_button.disabled = current_page == 0
                next_button.disabled = current_page == total_pages - 1
                await interaction.message.edit(embed=create_embed(current_page), view=view)
                
            prev_button.callback = previous_callback
            next_button.callback = next_callback
            next_button.disabled = total_pages <= 1
            
            view.add_item(prev_button)
            view.add_item(next_button)
            
            await ctx.reply(embed=embed, view=view, mention_author=False)
        else:
            await ctx.reply(embed=embed, mention_author=False)

    @commands.command(name="warns", aliases=["warnings"])
    async def warns_cmd(self, ctx, member: nextcord.Member):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        config = config["moderation"]
        config = config["warn"]
        config = config.get(str(ctx.guild.id))
        if not config:
            return
        if not any(role in user_roles for role in config) and not ctx.author.guild_permissions.administrator:
            return
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        doc.pop("_id")
        doc.pop("current_case")
        if not doc:
            await ctx.reply("No warns found for this guild.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        page_size = 5
        warnings = []
        for case, data in doc.items():
            if int(data.get("member", 0)) == member.id:
                warnings.append({
                    "case_id": case,
                    "moderator": data.get("moderator"),
                    "reason": data.get("reason"),
                    "date": data.get("date")
                })

        if not warnings:
            await ctx.reply("No warns found for this user.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return

        total_pages = (len(warnings) + page_size - 1) // page_size
        current_page = 0

        def create_embed(page):
            embed = nextcord.Embed(title=f"Warnings for {member.name}", color=nextcord.Color.blurple())
            start = page * page_size
            end = start + page_size
            embed.description = f"**Total Warns:** `{len(warnings)}`\n**Event Warns:** `{len([warning for warning in warnings if '[Event Warn]' in warning['reason']])}`"
            for warning in warnings[start:end]:
                moderator = ctx.guild.get_member(warning['moderator'])
                embed.add_field(
                    name=f"Case #{warning['case_id']}",
                    value=f"**Moderator:** {moderator.name if moderator else str(warning['moderator'])} ({warning['moderator']})\n**Reason:** {warning['reason']}\n**Date:** {warning['date']}",
                    inline=False
                )
            embed.set_footer(text=f"Page {page + 1}/{total_pages}")
            return embed

        embed = create_embed(current_page)
        message = await ctx.reply(embed=embed, mention_author=False)

        if total_pages > 1:
            view = nextcord.ui.View()
            
            prev_button = nextcord.ui.Button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.gray)
            next_button = nextcord.ui.Button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.gray)
            
            prev_button.disabled = True
            
            async def previous_callback(interaction):
                nonlocal current_page
                if interaction.user != ctx.author:
                    return
                current_page = max(0, current_page - 1)
                prev_button.disabled = current_page == 0
                next_button.disabled = current_page == total_pages - 1
                await interaction.message.edit(embed=create_embed(current_page), view=view)

            async def next_callback(interaction):
                nonlocal current_page
                if interaction.user != ctx.author:
                    return
                current_page = min(total_pages - 1, current_page + 1)
                prev_button.disabled = current_page == 0
                next_button.disabled = current_page == total_pages - 1
                await interaction.message.edit(embed=create_embed(current_page), view=view)

            prev_button.callback = previous_callback
            next_button.callback = next_callback
            
            view.add_item(prev_button)
            view.add_item(next_button)

            await message.edit(view=view)
    @commands.command(name="removewarn", aliases=["rwarn", "deletewarn", "delwarn"])
    async def removewarn_cmd(self, ctx, warn_id: str = None, *, reason: str = "No reason provided"):
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
        await ctx.message.add_reaction(GREEN_CHECK)
        collection.update_one({"_id": f"warn_logs_{ctx.guild.id}"}, {"$unset": {str(warn_id): 1}})
        if logs:
            embed = nextcord.Embed(title=f"Member Warn Removed | Warn ID #{warn_id}", description=f"**Moderator:** {ctx.author.name} ({ctx.author.id})\n**Reason:** {reason}", color=nextcord.Color.blurple())
            embed.timestamp = datetime.now()
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass


    @commands.command(name="ebl", aliases=["eventblacklist"])
    async def ebl_cmd(self, ctx, member: nextcord.Member, duration: str = "1d", *, reason: str = "No reason provided"):
        if ctx.guild.id != 1205270486230110330:
            return
        if not ctx.author.guild_permissions.manage_messages:
            await ctx.message.add_reaction(RED_X)
            return
        if 1205270486469058636 in [role.id for role in ctx.author.roles]:
            await ctx.message.add_reaction(RED_X)
            return
        ebl_role = ctx.guild.get_role(1205270486359998556)
        if not ebl_role:
            await ctx.message.add_reaction(RED_X)
            return
        if ctx.author.top_role.position < member.top_role.position:
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(LOADING)
        if ebl_role in member.roles:
            await member.remove_roles(ebl_role)
            doc = collection.find_one({"_id": f"ebl_{ctx.guild.id}"})
            doc = doc.get(str(member.id))
            if doc:
                current_roles = member.roles
                roles = doc.get("roles")
                for role in roles:
                    the_role = ctx.guild.get_role(int(role))
                    if the_role:
                        current_roles.append(the_role)
                await member.edit(roles=current_roles)
            collection.update_one({"_id": f"ebl_{ctx.guild.id}"}, {"$unset": {str(member.id): ""}})
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title=f"Event Blacklist Removed", description=f"{member.mention} has been removed from the event blacklist.", color=nextcord.Color.green())
            await member.send("**Robbing Central:** You have been removed from the event blacklist.")
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)
        else:
            time, readable = await self.get_time_until_timeout(duration)
            if time == 0:
                await ctx.message.add_reaction(RED_X)
                return
            end = datetime.now() + timedelta(minutes=time // 60)
            if time is None:
                await ctx.message.add_reaction(RED_X)
                return
            roles_to_edit = member.roles
            member_roles = member.roles
            roles = []
            for role in member_roles:
                if "donor" in role.name.lower():
                    roles.append(role.id)
                    roles_to_edit.remove(role)
            await member.edit(roles=roles_to_edit)
            collection.update_one({"_id": f"ebl_{ctx.guild.id}"}, {"$set": {str(member.id): {"roles": roles, "end": end, "reason": reason}}}, upsert=True)
            await member.add_roles(ebl_role)
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title=f"Event Blacklist Added", description=f"{member.mention} has been blacklisted from events and giveaways for {readable}, for reason: {reason}", color=nextcord.Color.green())
            if "remove warns" in reason.lower() and "dont remove warns" not in reason.lower() and "don't remove warns" not in reason.lower():
                warns_cleared = await self.ebl_clearwarns(ctx, member)
                embed.description = f"{member.mention} has been blacklisted from events and giveaways for {readable}, for reason: {reason} and {warns_cleared} event warns have been removed."
            embed.set_footer(text=f"Execute this command again to remove the blacklist.")
            await member.send(f"**Robbing Central:** You have been blacklisted from events and giveaways for {readable}, for reason: {reason}")
            await ctx.reply(embed=embed, mention_author=False)
            await ctx.message.add_reaction(GREEN_CHECK)
        
    async def ebl_clearwarns(self, ctx, member):
        doc = collection.find_one({"_id": f"warn_logs_{ctx.guild.id}"})
        if not doc:
            return
        warns_cleared = 0
        for case, data in doc.items():
            if case == "current_case":
                continue
            if case == "_id":
                continue
            if int(data.get("member", 0)) == member.id and "[Event Warn]" in data.get("reason", ""):
                collection.update_one({"_id": f"warn_logs_{ctx.guild.id}"}, {"$unset": {str(case): 1}})
                warns_cleared += 1
        return warns_cleared
    
    @nextcord.slash_command(name="quarantine", description="Quarantine a user")
    async def quarantine(self, interaction: nextcord.Interaction):
        pass

    @quarantine.subcommand(name="add", description="Quarantine a user.")
    async def add(self, interaction: nextcord.Interaction, member: nextcord.Member, reason: Optional[str] = "No reason provided"):
        config = configuration.find_one({"_id": "config"})
        config = config["quarantine"]
        logs = config["logs"]
        logs = logs.get(str(interaction.guild.id))
        config = config.get(str(interaction.guild.id))
        if not config:
            await interaction.response.send_message(f"Quarantine is not configured for this server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"You do not have permission to quarantine users.", ephemeral=True)
            return
        if member.top_role.position >= interaction.user.top_role.position:
            await interaction.response.send_message(f"You do not have permission to quarantine this user.", ephemeral=True)
            return
        if member.top_role.position >= interaction.guild.me.top_role.position:
            await interaction.response.send_message(f"I do not have permission to quarantine this user.", ephemeral=True)
            return
        quarantine_role = interaction.guild.get_role(config)
        member_roles = [role.id for role in member.roles]
        if not quarantine_role:
            await interaction.response.send_message(f"Quarantine role is not configured for this server or the role does not exist.", ephemeral=True)
            return
        if quarantine_role.id in member_roles:
            await interaction.response.send_message(f"**{member.name}** is already quarantined.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        try:
            await member.edit(roles=[quarantine_role])
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to modify this user's roles.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            return
        collection.update_one(
            {"_id": f"quarantines_{interaction.guild.id}"}, 
            {"$set": {f"{member.id}": member_roles}},
            upsert=True
        )
        embed = nextcord.Embed(title=f"Member Quarantined", description=f"**User Quarantined:** {member.name} ({member.id})\n**Moderator:** {interaction.user.name} ({interaction.user.id})\n**Reason:** {reason}", color=nextcord.Color.green())
        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = datetime.now()
        await interaction.send(embed=embed, ephemeral=True)
        if logs:
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass
        

    @quarantine.subcommand(name="remove", description="Remove a user from quarantine.")
    async def remove(self, interaction: nextcord.Interaction, member: nextcord.Member, reason: Optional[str] = "No reason provided"):
        config = configuration.find_one({"_id": "config"})
        config = config["quarantine"]
        logs = config["logs"]
        logs = logs.get(str(interaction.guild.id))
        config = config.get(str(interaction.guild.id))

        if not config:
            await interaction.response.send_message(f"Quarantine is not configured for this server.", ephemeral=True)
            return
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(f"You do not have permission to remove users from quarantine.", ephemeral=True)
            return
        if member.top_role.position >= interaction.user.top_role.position:
            await interaction.response.send_message(f"You do not have permission to remove this user from quarantine.", ephemeral=True)
            return
        quarantine_role = interaction.guild.get_role(config)
        if not quarantine_role:
            await interaction.response.send_message(f"Quarantine role is not configured for this server or the role does not exist.", ephemeral=True)
            return
        member_roles = [role.id for role in member.roles]
        if not quarantine_role.id in member_roles:
            await interaction.response.send_message(f"**{member.name}** is not quarantined.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        backup_roles_doc = collection.find_one({"_id": f"quarantines_{interaction.guild.id}"})
        if not backup_roles_doc:
            await interaction.response.send_message("No role backup found for this server.", ephemeral=True)
            return
        backup_roles = backup_roles_doc.get(str(member.id))
        roles = []
        if backup_roles:
            for role_id in backup_roles:
                role = interaction.guild.get_role(int(role_id))
                if role:
                    roles.append(role)
        try:
            await member.edit(roles=roles)
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to modify this user's roles.", ephemeral=True)
            return
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
            return
        try:
            collection.update_one(
                {"_id": f"quarantines_{interaction.guild.id}"}, 
                {"$unset": {f"{member.id}": 1}}
            )
        except Exception as e:
            await interaction.response.send_message(f"Failed to update database: {str(e)}", ephemeral=True)
            return
        embed = nextcord.Embed(title=f"Member Quarantine Removed", description=f"**User Quarantined:** {member.name} ({member.id})\n**Moderator:** {interaction.user.name} ({interaction.user.id})\n**Reason:** {reason}", color=nextcord.Color.red())
        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = datetime.now()
        await interaction.send(embed=embed, ephemeral=True)
        if logs:
            logs = self.bot.get_channel(int(logs))
            try:
                await logs.send(embed=embed)
            except:
                pass
        
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

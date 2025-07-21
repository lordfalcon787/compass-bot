import random
import nextcord
import asyncio

from fuzzywuzzy import fuzz
from datetime import datetime, timedelta
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection

GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
CHANNELS = [1205270487454974061, 1214594429575503912, 1240782193270460476, 1286101587965775953, 1219081468458831992, 1291161396368773183]
VALID_CHANNELS = [1205270487454974061, 1214594429575503912, 1286101587965775953, 1291161396368773183, 1219081468458831992, 1205270487274496054]
RUMBLE_ROYALE = 693167035068317736
WORDS = ["gtn", "gti", "gartic", "wordle"]
RC_ID = 1205270486230110330

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]
reminder_collection = db["Reminders"]

class View(nextcord.ui.View):
    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)
        button = nextcord.ui.Button(label="Members with Role", style=nextcord.ButtonStyle.primary)
        button.callback = self.members_with_role
        self.add_item(button)

    async def members_with_role(self, interaction):
        id = interaction.message.embeds[0].footer.text.split(" ")[1]
        role = interaction.guild.get_role(int(id))
        members = role.members
        descp = ""
        member_count = len(members)
        count = 0
        for member in members:
            if len(descp) > 1900:
                descp = f"{descp}\n`+{member_count - count}` more members."
                break
            descp = f"{descp}\n`{member.name}` | {member.mention}"
            count += 1
        await interaction.response.send_message(content=descp, ephemeral=True)

class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @tasks.loop(hours=1)
    async def reminder_task(self):
        docs = reminder_collection.find()
        for doc in docs:
            if doc["end_time"] < datetime.now() + timedelta(hours=1):
                asyncio.create_task(self.reminder_fulfilled(doc))

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Utility cog loaded.")
        self.bot.add_view(View())

    @commands.command(name="reminder", aliases=["remind", "rm"])
    async def reminder_cmd(self, ctx, time, *, message=None):
        if time.lower() == "list":
            await self.list_reminders(ctx)
            return
        if time.lower() == "delete":
            await self.delete_reminder(ctx)
            return
        if message is None:
            await ctx.reply("Please specify a reminder message.", mention_author=False)
            return
        date_formats = ["%m/%d/%Y", "%m/%d/%y", "%m/%d"]
        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(time, fmt)
                if fmt == "%m/%d":
                    parsed_date = parsed_date.replace(year=datetime.now().year)
                    if parsed_date < datetime.now():
                        parsed_date = parsed_date.replace(year=parsed_date.year + 1)
                break
            except ValueError:
                continue

        if parsed_date:
            now = datetime.now()
            total_seconds = int((parsed_date - now).total_seconds())
            if total_seconds < 0:
                total_seconds = 0
        else:
            time_expr = time.replace("y", "*31536000+").replace("w", "*604800+").replace("d", "*86400+").replace("h", "*3600+").replace("m", "*60+").replace("s", "*1+")
            if time_expr.endswith('+'):
                time_expr = time_expr[:-1]
            try:
                total_seconds = int(eval(time_expr))
            except Exception:
                total_seconds = 0
        end_time = datetime.now() + timedelta(seconds=total_seconds)
        current_reminder_id = reminder_collection.find_one({"_id": "current_reminder_id"})
        if not current_reminder_id:
            current_reminder_id = 1
        else:
            current_reminder_id = current_reminder_id["current_reminder_id"]
        current_reminder_id += 1
        reminder_collection.update_one({"_id": "current_reminder_id"}, {"$set": {"current_reminder_id": current_reminder_id}})
        reminder_data = {
            "_id": ctx.message.id,
            "sent_time": datetime.now(),
            "end_time": end_time,
            "user": ctx.author.id,
            "channel": ctx.channel.id,
            "guild": ctx.guild.id,
            "reminder_id": current_reminder_id,
            "reminder": message
        }
        reminder_collection.insert_one(reminder_data)
        def format_time(seconds):
            periods = [
                ('year', 31536000),
                ('month', 2592000),
                ('week', 604800),
                ('day', 86400),
                ('hour', 3600),
                ('minute', 60),
                ('second', 1)
            ]
            strings = []
            for period_name, period_seconds in periods:
                if seconds >= period_seconds:
                    period_value, seconds = divmod(seconds, period_seconds)
                    if period_value == 1:
                        strings.append(f"{period_value} {period_name}")
                    else:
                        strings.append(f"{period_value} {period_name}s")
            if not strings:
                return "0 seconds"
            if len(strings) == 1:
                return strings[0]
            else:
                return f"{', '.join(strings[:-1])} and {strings[-1]}"
        time_str = format_time(total_seconds)
        embed = nextcord.Embed(title=f"Reminder #{current_reminder_id} Created", description=f"Of course, **{ctx.author.name}**, I will remind you in **{time_str}** about:\n\n{message}", color=nextcord.Color.blurple())
        if total_seconds < 3600:
            asyncio.create_task(self.reminder_fulfilled(reminder_data))
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(embed=embed, mention_author=False)

    async def list_reminders(self, ctx):
        import math
        from nextcord.ui import View, Button

        docs = list(reminder_collection.find({"user": ctx.author.id}))
        if not docs:
            await ctx.reply("There are no reminders set.", mention_author=False)
            return

        reminders_per_page = 10
        total_pages = math.ceil(len(docs) / reminders_per_page)

        def get_embed(page):
            start = page * reminders_per_page
            end = start + reminders_per_page
            embed = nextcord.Embed(
                title=f"Reminders (Page {page+1}/{total_pages})",
                color=nextcord.Color.blurple()
            )
            for doc in docs[start:end]:
                user = self.bot.get_user(doc['user'])
                user_mention = user.mention if user else f"<@{doc['user']}>"
                channel_mention = f"<#{doc['channel']}>"
                reminder_text = doc.get('reminder', 'No reminder text')
                embed.add_field(
                    name=f"Reminder #{doc['reminder_id']}",
                    value=f"By: {user_mention}\nIn: {channel_mention}\nAbout: {reminder_text}",
                    inline=False
                )
            embed.set_footer(text="Use the buttons below to navigate pages.")
            return embed

        class RemindersView(View):
            def __init__(self, author, timeout=60):
                super().__init__(timeout=timeout)
                self.page = 0
                self.author = author

            async def interaction_check(self, interaction):
                return interaction.user.id == self.author.id

            @Button(label="Previous", style=nextcord.ButtonStyle.primary, emoji="⬅️", disabled=True)
            async def previous(self, button: Button, interaction: nextcord.Interaction):
                self.page -= 1
                if self.page == 0:
                    self.previous.disabled = True
                self.next.disabled = False
                await interaction.response.edit_message(embed=get_embed(self.page), view=self)

            @Button(label="Next", style=nextcord.ButtonStyle.primary, emoji="➡️", disabled=(total_pages <= 1))
            async def next(self, button: Button, interaction: nextcord.Interaction):
                self.page += 1
                if self.page == total_pages - 1:
                    self.next.disabled = True
                self.previous.disabled = False
                await interaction.response.edit_message(embed=get_embed(self.page), view=self)

        view = RemindersView(ctx.author)
        await ctx.reply(embed=get_embed(0), view=view, mention_author=False)

    async def delete_reminder(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) < 3:
            await ctx.send("Please specify a reminder ID to delete.")
            return
        reminder_id = split[2]
        reminder_collection.delete_one({"reminder_id": reminder_id})
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.reply(f"Reminder #{reminder_id} deleted.", mention_author=False)

    async def reminder_fulfilled(self, reminder_data):
        doc = reminder_collection.find_one({"_id": reminder_data["_id"]})
        if not doc:
            return
        time_left = (reminder_data["end_time"] - datetime.now()).total_seconds()
        if time_left < 0:
            time_left = 0
        await asyncio.sleep(time_left)
        time_ago = datetime.now() - reminder_data["sent_time"]
        seconds = int(time_ago.total_seconds())
        periods = [
            ('year', 31536000),
            ('month', 2592000),
            ('week', 604800),
            ('day', 86400),
            ('hour', 3600),
            ('minute', 60),
            ('second', 1)
        ]
        strings = []
        for period_name, period_seconds in periods:
            if seconds >= period_seconds:
                period_value, seconds = divmod(seconds, period_seconds)
                if period_value == 1:
                    strings.append(f"{period_value} {period_name}")
                else:
                    strings.append(f"{period_value} {period_name}s")
        if not strings:
            time_ago_str = "just now"
        else:
            time_ago_str = " ".join(strings) + " ago"
        embed = nextcord.Embed(title=f"Reminder #{reminder_data['reminder_id']}", description=f'You asked to be reminded about "{reminder_data["reminder"]}" **{time_ago_str}**.', color=nextcord.Color.blurple())
        embed.add_field(name="Activation Message", value=f"https://discord.com/channels/{reminder_data['guild']}/{reminder_data['channel']}/{reminder_data['_id']}")
        user = self.bot.get_user(reminder_data["user"])
        if not user:
            reminder_collection.delete_one({"_id": reminder_data["_id"]})
            return
        try:
            reminder_collection.delete_one({"_id": reminder_data["_id"]})
            await user.send(embed=embed)
        except:
            pass

    def get_best_match(self, members, args):
        name_dict = {}
        display_name_dict = {}
        for member in members:
            try:
                if args.lower() in member.name.lower():
                    name_dict[member] = fuzz.ratio(args.lower(), member.name.lower())
            except:
                pass
            try:
                if args.lower() in member.display_name.lower():
                    display_name_dict[member] = fuzz.ratio(args.lower(), member.display_name.lower())
            except:
                pass
        try:
            best_name = max(name_dict, key=name_dict.get)
        except:
            best_name = None
        try:
            best_display_name = max(display_name_dict, key=display_name_dict.get)
        except:
            best_display_name = None
        if best_name and best_display_name:
            dict = {
                best_name: name_dict[best_name],
                best_display_name: display_name_dict[best_display_name]
            }
            return max(dict, key=dict.get)
        elif best_name:
            return best_name
        elif best_display_name:
            return best_display_name
        else:
            return None
    
    async def user_info(self, message):
        if len(message.content.split(" ")) == 1:
            member = message.author
        else:
            args = message.content.split(" ")[1:]
            args = " ".join(args)
            args = args.replace("<", "").replace(">", "").replace("@", "")
            if args.isdigit():
                try:
                    member = await message.guild.fetch_member(int(args))
                except:
                    await message.channel.send(embed=nextcord.Embed(description=f"{RED_X} No members with the provided ID were found.", color=nextcord.Color.red()))
                    return
            else:
                member = self.get_best_match(message.guild.members, args)
        if not member:
            await message.channel.send(embed=nextcord.Embed(description=f"{RED_X} No members with the provided name were found.", color=nextcord.Color.red()))
            return


        embed = nextcord.Embed(description=member.mention, color=member.color)
        try:
            embed.set_author(name=member.name, icon_url=member.avatar.url)
        except:
            embed.set_author(name=member.name)
        try:
            embed.set_thumbnail(url=member.display_avatar.url)
        except:
            pass
        embed.add_field(name="Joined Server", value=member.joined_at.strftime('%d %B %Y %H:%M UTC'), inline=True)
        embed.add_field(name="Created At", value=member.created_at.strftime('%d %B %Y %H:%M UTC'), inline=True)

        sorted_roles = sorted([role for role in member.roles if not role.is_default()], key=lambda r: r.position, reverse=True)
        role_mentions = [role.mention for role in sorted_roles[:42]]
        additional_roles = len(member.roles) - 42
        roles_value = " ".join(role_mentions) + (f" `+{additional_roles}`" if additional_roles > 0 else "")
        embed.add_field(name=f"Roles [{len(member.roles) - 1}]", value=roles_value, inline=False)

        perms = [
            perm.replace('_', ' ').title()
            for perm, value in member.guild_permissions
            if value and any(keyword in perm.replace('_', ' ').lower() for keyword in ["manage", "administrator", "mention"])
        ]
        embed.add_field(name="Key Permissions", value=", ".join(perms) if perms else "None", inline=False)

        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = datetime.utcnow()
        await message.channel.send(embed=embed)

    @commands.command(name="creset")
    async def creset_cmd(self, ctx):
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        overwrite = ctx.channel.overwrites_for(ctx.guild.default_role)
        overwrite.view_channel = None
        await ctx.channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(1)
        await ctx.message.delete()

    @commands.command(name="userinfo", aliases=["ui", "w", "whois"])
    async def userinfo_cmd(self, ctx):
        await self.user_info(ctx.message)
        return
        
    async def rumble(self, message):
        if not message.embeds:
            return
        
        embed = message.embeds[0]
        embed_title = embed.title
        embed_description = embed.description

        doc = configuration.find_one({"_id": "config"})
        doc = doc["auto_lock"]
        guild = str(message.guild.id)
        if guild not in doc:
            return
        
        doc = doc[guild]

        if "status" not in doc:
            return
        elif not doc["status"]:
            return
        elif "channels" not in doc:
            return
        elif message.channel.id not in doc["channels"]:
            return
        
        if not embed_title or not embed_description:
            return

        if "Rumble Royale" in embed_title:
            if "Starting in 15 seconds." in embed_description:
                await self.unlock_module(message)
            elif "Starting in 22 seconds." in embed_description:
                await self.unlock_module(message)
            elif "Starting in 37 seconds." in embed_description:
                await asyncio.sleep(18)
                await self.unlock_module(message)
            else:
                return
        elif "WINNER" in embed_title:
            await self.lock_module(message)
        else:
            return
        
    @commands.command(name="ul")
    async def ul_cmd(self, message):
        await self.u_module(message)
        return
    
    @commands.command(name="l")
    async def l_cmd(self, message):
        await self.l_module(message)
        return
    
    @commands.command(name="unlock")
    async def unlock_cmd(self, message):
        await self.u_module(message)
        return
    
    @commands.command(name="lock")
    async def lock_cmd(self, message):
        await self.l_module(message)
        return
    
    @commands.command(name="purge")
    async def purge_messages(self, ctx, amount: int):
        if not ctx.author.guild_permissions.manage_messages:
            return
        try:
            amount = int(ctx.message.content.split(None, 1)[1])
        except (IndexError, ValueError):
            await ctx.send("Please specify the number of messages to purge. Usage: `-purge [number]`")
            return
        if amount <= 0 or amount > 100:
            await ctx.send("Please specify a number between 1 and 100.")
            return
        await ctx.message.add_reaction("<a:loading_animation:1218134049780928584>")
        deleted = await ctx.channel.purge(limit=amount + 1)
        
        user_counts = {}
        for msg in deleted[1:]:
            user_counts[msg.author.name] = user_counts.get(msg.author.name, 0) + 1
                
        confirmation_text = f"Purged **{len(deleted) - 1}** messages:\n"
        confirmation_text += "\n".join(f"**{user}:** `{count}`" for user, count in user_counts.items())
            
        confirmation = await ctx.send(confirmation_text)
        await asyncio.sleep(3)
        await confirmation.delete()
    async def unlock_module(self, message):
        overwrites = message.channel.overwrites_for(message.guild.default_role)
        if overwrites.send_messages is None or overwrites.send_messages is True:   
            return
        overwrites.send_messages = None
        await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
        await message.channel.send(f":white_check_mark: Unlocked **{message.channel.name}**")
        await asyncio.sleep(1)

    async def lock_module(self, message):
        overwrites = message.channel.overwrites_for(message.guild.default_role)
        if overwrites.send_messages is False:   
            return
        overwrites.send_messages = False
        await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
        await message.channel.send(f":white_check_mark: Locked **{message.channel.name}**")
        await asyncio.sleep(1)

    @commands.command(name="avatar", aliases=["av"])
    async def avatar_cmd(self, message):
        await self.avatar(message)
        return
        
    async def avatar(self, message):
        arg = message.content.split(" ")

        if len(arg) == 1:
            embed = nextcord.Embed(title="Server Avatar", color=message.author.color)
            avatar = message.author.display_avatar
            if avatar is None:
                embed.set_author(name=message.author.name)
                embed.description = f"No avatar found for {message.author.name}"
                await message.channel.send(embed=embed)
                return
            embed.set_image(url=avatar.url)
            embed.set_author(name=message.author.name, icon_url=avatar.url)
            await message.channel.send(embed=embed)
        else:
            arg = arg[1]
            arg = arg.replace("<", "").replace(">", "").replace("@", "")
            if arg.isdigit():
                member = await message.guild.fetch_member(int(arg))
            else:
                member = next((m for m in message.guild.members if arg.lower() in m.name.lower()), None)
            if member:
                embed = nextcord.Embed(title=f"Server Avatar", color=member.color)
                avatar = member.display_avatar
                if avatar is None:
                    embed.set_author(name=member.name)
                    embed.description = f"No avatar found for {member.name}"
                    await message.channel.send(embed=embed)
                    return
                embed.set_author(name=member.name, icon_url=avatar.url)
                embed.set_image(url=avatar.url)
                await message.channel.send(embed=embed)

    async def l_module(self, message):
        config = db["Configuration"]
        doc = config.find_one({"_id": "config"})
        guild = str(message.guild.id)
        access = []
        user_roles = [role.id for role in message.author.roles]
        if guild in doc["lock_role"]:
            access = doc["lock_role"][guild]
        if not message.channel.permissions_for(message.author).manage_messages and not any(role in access for role in user_roles):
            return
        overwrites = message.channel.overwrites_for(message.guild.default_role)
        if overwrites.send_messages is False:   
            await message.channel.send(f"{RED_X} This channel is already locked.")
            await message.message.add_reaction(RED_X)
            await asyncio.sleep(1)
            await message.message.delete()
            return
        
        overwrites.send_messages = False
        await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
        await message.channel.send(f":white_check_mark: Locked {message.channel.name}")
        await message.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(1)
        await message.message.delete()

    async def u_module(self, message):
        config = db["Configuration"]
        doc = config.find_one({"_id": "config"})
        guild = str(message.guild.id)
        access = []
        user_roles = [role.id for role in message.author.roles]
        if guild in doc["lock_role"]:
            access = doc["lock_role"][guild]
        if not message.channel.permissions_for(message.author).manage_messages and not any(role in access for role in user_roles):
            return
        overwrites = message.channel.overwrites_for(message.guild.default_role)
        if overwrites.send_messages is None or overwrites.send_messages is True:   
            await message.channel.send(f"{RED_X} This channel is already unlocked.")
            await message.message.add_reaction(RED_X)
            await asyncio.sleep(1)
            await message.message.delete()
            return
        overwrites.send_messages = None
        await message.channel.set_permissions(message.guild.default_role, overwrite=overwrites)
        await message.channel.send(f":white_check_mark: Unlocked **{message.channel.name}**")
        await message.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(1)
        await message.message.delete()

    @commands.command(name="dm")
    async def dm(self, ctx, member: nextcord.Member, *, message):
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.send(f"**{ctx.guild.name}:** {message}")
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(GREEN_CHECK)
        except nextcord.Forbidden:
            await ctx.send(f"Failed to send DM to {member.mention}. Make sure I'm not blocked and have the necessary permissions.")
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(RED_X)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(RED_X)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id == RUMBLE_ROYALE:
            asyncio.create_task(self.rumble(message))

        if "cumpass" in message.content.lower():
            if message.author.id == 1149719763388477481:
                return
            array = [
                "I don't like you.",
                "Did you know it's disrespectful to not call people by their proper name?",
                "I hate you.", 
                "Please die.", 
                "It's an o not a u.", 
                "Enjoy your 10 second timeout!", 
                "Wishing you a delightful 30 second timeout!", 
                "Hope you enjoy your 60 second timeout!",
                "Have fun with your 10 second timeout!",
                "Have fun with your 30 second timeout!",
                "Have fun with your 60 second timeout!",
                "You deserve an award. A 10 second timeout.",
                "You deserve an award. A 30 second timeout.",
                "You deserve an award. A 60 second timeout.",
                "I hate you so much I gave you a 10 second timeout.",
                "I hate you so much I gave you a 30 second timeout.",
                "I hate you so much I gave you a 60 second timeout.",
                "You're the absolute worst.", 
                "I can't stand your presence.", 
                "You're incredibly annoying.", 
                "I wish you'd just vanish.", 
                "You're far from my favorite person.", 
                "I genuinely dislike you.", 
                "You're a real pain in the neck.", 
                "I don't want you around.", 
                "You're just too much to handle.",
                "If you were any more basic, you'd be a factory setting.",
                "You're like a software update; I see you and think, 'Not now.'",
                "I'd explain it to you, but I left my English-to-Dingbat dictionary at home.",
                "You're proof that even evolution has its blunders.",
                "You're like a cloud; when you disappear, it's a beautiful day.",
                "I'd call you a tool, but that implies you're actually useful.",
                "You're the reason God created the middle finger.",
                "You're like a broken pencil: pointless.",
                "If laughter is the best medicine, your face must be curing the world.",
                "You're like a software bug; I can't get rid of you no matter how hard I try.",
                "You're like a participation trophy; you exist, but no one really wants you.",
                "You're the human equivalent of a typo.",
                "You're like a candle in the wind—useless and annoying.",
                "If ignorance is bliss, you must be the happiest person alive.",
                "You're like a Wi-Fi signal; weak and unreliable.",
                "You're the reason they put instructions on shampoo.",
                "You're like a slinky; not really good for much, but fun to watch fall down the stairs.",
                "You're like a software update; I dread seeing you.",
                "You're the reason God created the middle finger.",
                "You're like a broken clock; right twice a day, but still broken.",
                "You're like a black hole; you suck the joy out of everything.",
                "You're the punchline to a joke that nobody wants to hear."
            ]
            choice = random.choice(array)
            if "timeout" in choice and "10" in choice and not message.author.guild_permissions.administrator:
                member = message.guild.get_member(message.author.id)
                time = datetime.now() + timedelta(seconds=10)
                await member.edit(timeout=time)
            elif "timeout" in choice and "30" in choice and not message.author.guild_permissions.administrator:
                member = message.guild.get_member(message.author.id)
                time = datetime.now() + timedelta(seconds=30)
                await member.edit(timeout=time)
            elif "timeout" in choice and "60" in choice and not message.author.guild_permissions.administrator:
                member = message.guild.get_member(message.author.id)
                time = datetime.now() + timedelta(seconds=60)
                await member.edit(timeout=time)
            await message.reply(choice, mention_author=False)
            
        elif any(word in message.content.lower() for word in WORDS) and "<@&1205270486263795720>" in message.content:
            asyncio.create_task(self.unlock_module(message))
            return
        elif message.content.startswith("?av"):
            asyncio.create_task(self.avatar(message))
            return
        elif message.content.startswith("?w") and message.guild.id == RC_ID:
            if not message.content.startswith("?w ") and len(message.content.split(" ")) > 1:
                return
            asyncio.create_task(self.user_info(message))

def setup(bot):
    bot.add_cog(utility(bot))
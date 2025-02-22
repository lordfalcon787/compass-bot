import random
import nextcord
import asyncio

from fuzzywuzzy import fuzz
from nextcord.ext import commands
from datetime import datetime, timedelta
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

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Utility cog loaded.")
        self.bot.add_view(View())

    def get_best_match(self, members, args):
        best_match = None
        highest_ratio = 0
        for member in members:
            ratios = [
                fuzz.ratio(args.lower(), member.name.lower()),
                fuzz.ratio(args.lower(), member.display_name.lower()),
                fuzz.ratio(args.lower(), member.nick.lower() if member.nick else "")
            ]
            max_ratio = max(ratios)
            if max_ratio > highest_ratio:
                highest_ratio = max_ratio
                best_match = member
        return best_match
    
    async def user_info(self, message):
        if len(message.content.split(" ")) == 1:
            member = message.author
        else:
            args = message.content.split("?w ")[1]
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
        embed.add_field(name="Joined Server", value=member.joined_at.strftime('%d %B %H:%M UTC'), inline=True)
        embed.add_field(name="Created At", value=member.created_at.strftime('%d %B %H:%M UTC'), inline=True)

        sorted_roles = sorted([role for role in member.roles if not role.is_default()], key=lambda r: r.position, reverse=True)
        role_mentions = [role.mention for role in sorted_roles[:42]]
        additional_roles = len(member.roles) - 42
        roles_value = " ".join(role_mentions) + (f" `+{additional_roles}`" if additional_roles > 0 else "")
        embed.add_field(name=f"Roles [{len(member.roles)}]", value=roles_value, inline=False)

        perms = [
            perm.replace('_', ' ').title()
            for perm, value in member.guild_permissions
            if value and any(keyword in perm.replace('_', ' ').lower() for keyword in ["manage", "administrator", "mention"])
        ]
        embed.add_field(name="Key Permissions", value=", ".join(perms) if perms else "None", inline=False)

        embed.set_footer(text=f"ID: {member.id}")
        embed.timestamp = datetime.utcnow()
        await message.channel.send(embed=embed)

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
        
    async def avatar(self, message):
        arg = message.content.split(" ")

        if len(arg) == 1:
            embed = nextcord.Embed(title="Server Avatar", color=message.author.color)
            avatar = message.author.guild_avatar
            if avatar is None:
                avatar = message.author.avatar.url
            else:
                avatar = avatar.url
            embed.set_image(url=avatar)
            embed.set_author(name=message.author.name, icon_url=avatar)
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
                avatar = member.guild_avatar
                if avatar is None:
                    try:
                        avatar = member.avatar.url
                    except:
                        avatar = self.bot.user.avatar.url
                else:
                    avatar = avatar.url
                embed.set_image(url=avatar)
                embed.set_author(name=member.name, icon_url=avatar)
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
            await member.send(f"**Robbing Central:** {message}")
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
            await self.rumble(message)

        if "haha" in message.content.lower():
            try:
                await message.add_reaction("😆")
            except:
                pass
            return
        elif "cumpass" in message.content.lower():
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
            await self.unlock_module(message)
            return
        elif message.content.startswith("?av"):
            await self.avatar(message)
            return
        elif message.content.startswith("?w") and message.guild.id == RC_ID:
            if not message.content.startswith("?w ") and len(message.content.split(" ")) > 1:
                return
            await self.user_info(message)

def setup(bot):
    bot.add_cog(utility(bot))
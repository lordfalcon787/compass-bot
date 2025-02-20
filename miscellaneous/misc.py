import nextcord
import random
import nextcord.ext.commands
from nextcord.ext import commands, application_checks, tasks
from typing import Optional
from nextcord import SlashOption
from utils.mongo_connection import MongoConnection
import json
from PIL import Image, ImageDraw, ImageOps, ImageFont
import aiohttp
from io import BytesIO

with open("config.json", "r") as file:
    config = json.load(file)

BOT_TOKEN = config["bot_token"]
RETRIEVE_MONGO = config["db_token"]
TESTING_GUILD_ID = 1234605482937684059
RC_ID = 1205270486230110330
RC_AUCTION_QUEUE = 1267530934723281009
RC_EVENT_QUEUE = 1267527896218468412
EVENT_QUEUE = 1266257466677792768
AUCTION_QUEUE = 1267355852856229918
RC_ICON = "https://i.imgur.com/K5L7kxl.png"
RC_BANNER = "https://i.imgur.com/kL6BSmK.jpeg"
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
misccollection = db["Misc"]
masters = db["Masters"]

class misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Miscellaneous cog loaded.")

    @tasks.loop(minutes=5)
    async def update_masters_event(self):
       pass 

    @commands.command(name="add")
    async def add_points(self, ctx, user: nextcord.Member, points: int):
        role = 1333518413431050330
        role_2 = 1205270486469058637
        roles = [role.id for role in ctx.author.roles]
        if role not in roles and role_2 not in roles:
            await ctx.message.add_reaction(RED_X)
            return
        masters.update_one({"_id": "masters_event"}, {"$inc": {f"{user.id}": points}}, upsert=True)
        await ctx.reply(f"Added `{points}` points to {user.mention}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="remove")
    async def remove_points(self, ctx, user: nextcord.Member, points: int):
        role = 1333518413431050330
        role_2 = 1205270486469058637
        roles = [role.id for role in ctx.author.roles]
        if role not in roles and role_2 not in roles:
            await ctx.message.add_reaction(RED_X)
            return
        masters.update_one({"_id": "masters_event"}, {"$inc": {f"{user.id}": -points}}, upsert=True)
        await ctx.reply(f"Removed `{points}` points from {user.mention}", mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="mastersevent")
    async def mastersevent(self, ctx):
        team_choco = ctx.guild.get_role(1341576933984436334).members
        team_moon = ctx.guild.get_role(1341576995019948112).members
        
        choco_descp = "**Team Choco Members:**\n"
        for num, member in enumerate(team_choco, start=1):
            choco_descp = f"{choco_descp}\n{num}. {member.mention}"

        moon_descp = "**Team Moon Members:**\n"
        for num, member in enumerate(team_moon, start=1):
            moon_descp = f"{moon_descp}\n{num}. {member.mention}"

        embed_1 = nextcord.Embed(title="Masters Event", color=nextcord.Color.yellow())
        embed_1.description = choco_descp
        embed_1.timestamp = nextcord.utils.utcnow()
        embed_1.set_footer(icon_url=RC_ICON, text="Robbing Central Masters Event")

        embed_2 = nextcord.Embed(title="Masters Event", color=nextcord.Color.yellow())
        embed_2.description = moon_descp
        embed_2.timestamp = nextcord.utils.utcnow()
        embed_2.set_footer(icon_url=RC_ICON, text="Robbing Central Masters Event")
        
        team_choco_button = nextcord.ui.Button(label="Team Choco", style=nextcord.ButtonStyle.primary)
        team_moon_button = nextcord.ui.Button(label="Team Moon", style=nextcord.ButtonStyle.primary)

        @team_choco_button.callback
        async def team_choco_callback(interaction):
            if interaction.author != ctx.author:
                await interaction.response.send_message("You are not the original author of this command.", ephemeral=True)
                return
            await interaction.response.edit_message(embed=embed_1)

        @team_moon_button.callback
        async def team_moon_callback(interaction):
            if interaction.author != ctx.author:
                await interaction.response.send_message("You are not the original author of this command.", ephemeral=True)
                return
            await interaction.response.edit_message(embed=embed_2)

        view = nextcord.ui.View()
        team_choco_button.callback = team_choco_callback
        team_moon_button.callback = team_moon_callback
        view.add_item(team_choco_button)
        view.add_item(team_moon_button)
        await ctx.reply(embed=embed_1, view=view, mention_author=False)

    @commands.command(name="check")
    async def check_registered(self, ctx):
        role = ctx.guild.get_role(1337099004391063625)
        team_choco = ctx.guild.get_role(1341576933984436334)
        team_moon = ctx.guild.get_role(1341576995019948112)
        non_team_members = [member for member in role.members if team_choco not in member.roles and team_moon not in member.roles]
        descp = "**Members without a team:**\n"
        num = 1
        for member in non_team_members:
            descp = f"{descp}\n{num}. {member.mention}"
            num += 1
        embed = nextcord.Embed(title="Members Without a Team", description=descp, color=nextcord.Color.red())
        embed.timestamp = nextcord.utils.utcnow()
        embed.set_footer(icon_url=RC_ICON, text="Robbing Central Masters Event")
        await ctx.reply(embed=embed, mention_author=False)
            
    @commands.command(name="masterslb")
    async def masterslb(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            type = "users"
        else:
            type = split[1].lower()
        if "user" in type:
            await self.masterslbusers(ctx)
        elif "team" in type:
            team_choco = ctx.guild.get_role(1341576933984436334)
            team_moon = ctx.guild.get_role(1341576995019948112)
            doc = masters.find_one({"_id": "masters_event"})
            if doc is None:
                await ctx.reply("No users have any points.", mention_author=False)
                return
            doc.pop("_id")
            choco_points = 0
            moon_points = 0
            for user_id, points in doc.items():
                member = ctx.guild.get_member(int(user_id))
                if member is None:
                    continue
                if team_choco in member.roles:
                    choco_points += points
                elif team_moon in member.roles:
                    moon_points += points
            sorted_dict = {"Team Choco": choco_points, "Team Moon": moon_points}
            sorted_dict = dict(sorted(sorted_dict.items(), key=lambda item: item[1], reverse=True))
            descp = ""
            num = 1
            for team, points in sorted_dict.items():
                descp = f"{descp}\n{num}. **{team}** | {points} Points\n\n"
                num += 1
            embed = nextcord.Embed(title="Masters Teams Leaderboard", description=descp, color=nextcord.Color.yellow())
            embed.timestamp = nextcord.utils.utcnow()
            embed.set_image(url=RC_BANNER)
            embed.set_footer(icon_url=RC_ICON, text="Robbing Central Masters Event")
            await ctx.reply(embed=embed, mention_author=False)
    
    async def masterslbusers(self, ctx):
        doc = masters.find_one({"_id": "masters_event"})
        if doc is None:
            await ctx.reply("No users have any points.", mention_author=False)
            return
        doc.pop("_id")
        sorted_users = sorted(doc.items(), key=lambda x: x[1], reverse=True)
        total_users = len(sorted_users)
        total_pages = (total_users + 9) // 10 

        page = 1
        start_index = (page - 1) * 10
        end_index = start_index + 10
        users_to_display = sorted_users[start_index:end_index]

        descp = ""
        num = start_index + 1
        for user_id, points in users_to_display:
            descp += f"{num}. <@{user_id}> | {points} Points\n"
            num += 1

        embed = nextcord.Embed(title="Masters Users Leaderboard", description=descp, color=nextcord.Color.yellow())
        embed.timestamp = nextcord.utils.utcnow()
        embed.set_footer(icon_url=RC_ICON, text="Robbing Central Masters Event")
        view = nextcord.ui.View()
        previous_button = nextcord.ui.Button(emoji="<a:arrow_left:1316079524710191156>", style=nextcord.ButtonStyle.primary, custom_id="prev_page", disabled=True)
        next_button = nextcord.ui.Button(emoji="<a:arrow_right:1316079547124285610>", style=nextcord.ButtonStyle.primary, custom_id="next_page")
        if total_pages == 1:
            next_button.disabled = True

        async def prev_page_callback(interaction):
            nonlocal page
            page -= 1
            await update_leaderboard(interaction)

        async def next_page_callback(interaction):
            nonlocal page
            page += 1
            await update_leaderboard(interaction)

        async def update_leaderboard(interaction):
            if interaction.user != ctx.author:
                await interaction.response.send_message("You are not the original author of this command.", ephemeral=True)
                return
            nonlocal sorted_users
            start_index = (page - 1) * 10
            end_index = start_index + 10
            users_to_display = sorted_users[start_index:end_index]

            descp = ""
            num = start_index + 1
            for user_id, points in users_to_display:
                descp += f"{num}. <@{user_id}> | {points} Points\n"
                num += 1

            embed.description = descp

            for button in view.children:
                button.disabled = False
            view.children[0].disabled = (page == 1)
            view.children[1].disabled = (page == total_pages)

            await interaction.response.edit_message(embed=embed, view=view)

        previous_button.callback = prev_page_callback
        next_button.callback = next_page_callback
        view.add_item(previous_button)
        view.add_item(next_button)
        await ctx.reply(embed=embed, mention_author=False, view=view)
            
    @nextcord.slash_command(name="slowmode", description="Set slowmode for a channel")
    @application_checks.guild_only()
    async def slowmode(self, interaction: nextcord.Interaction, channel: Optional[nextcord.TextChannel] = None, seconds: int = 0):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if channel is None:
            channel = interaction.channel
        await channel.edit(slowmode_delay=seconds)
        await interaction.response.send_message(f"Slowmode for {channel.mention} has been set to {seconds} seconds.", ephemeral=True)

    @nextcord.slash_command(name="echo", description="Echo a message")
    @application_checks.guild_only()
    async def echo(self, interaction: nextcord.Interaction, 
                   message: str,
                   channel: Optional[nextcord.TextChannel] = None, 
                   reply: Optional[str] = SlashOption(description="Enter a message ID to reply to the user.", required=False)):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != 748339732605436055:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if channel is None:
            channel = interaction.channel
        try:
            if reply is not None:
                message_to_reply_to = await channel.fetch_message(int(reply))
                try:
                    msg = await message_to_reply_to.reply(message)
                    channellog = self.bot.get_channel(1266257466677792768)
                    embed = nextcord.Embed(title="Echo Logged", description=f"Guild: {interaction.guild.name}\nMessage URL: {msg.jump_url}\nMessage: `{message}`\nChannel: {channel.mention}\nUser: {interaction.user.mention}", color=0xff69b4)
                    await channellog.send(embed=embed)
                except nextcord.HTTPException as e:
                    await interaction.followup.send(f"Error sending message: {str(e)}", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"An unexpected error occurred: {str(e)}", ephemeral=True)
            else:
                try:
                    msg = await channel.send(message)
                    channellog = self.bot.get_channel(1266257466677792768)
                    embed = nextcord.Embed(title="Echo Logged", description=f"Guild: {interaction.guild.name}\nMessage URL: {msg.jump_url}\nMessage: `{message}`\nChannel: {channel.mention}\nUser: {interaction.user.mention}", color=0xff69b4)
                    await channellog.send(embed=embed)
                except nextcord.HTTPException as e:
                    await interaction.followup.send(f"Error sending message: {str(e)}", ephemeral=True)
                except Exception as e:
                    await interaction.followup.send(f"An unexpected error occurred: {str(e)}", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"An unexpected error occurred: {str(e)}", ephemeral=True)
        await interaction.response.send_message("Message sent.", ephemeral=True)

    @commands.command(name="choose")
    async def choose(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) < 3:
            await ctx.message.add_reaction(RED_X)
            return
        await ctx.message.add_reaction(GREEN_CHECK)
        await ctx.send(f"{random.choice(split[1:])}")

    @commands.command(name="resetallchannels")
    async def resetallchannels(self, ctx):
        if ctx.author.id != 1166134423146729563:
            await ctx.message.add_reaction(RED_X)
            return
        guild = self.bot.get_guild(RC_ID)
        await ctx.message.add_reaction("<a:loading_animation:1218134049780928584>")
        categories = ctx.message.content.split(" ")[1:]
        for category in categories:
            category = guild.get_channel(int(category))
            for channel in category.text_channels:
                perms = channel.overwrites_for(guild.default_role)
                perms.use_slash_commands = True
                await channel.set_permissions(guild.default_role, overwrite=perms)
        await ctx.message.clear_reactions()
        await ctx.message.add_reaction(GREEN_CHECK)

    async def get_avatar_image(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                avatar_bytes = await response.read()
                return Image.open(BytesIO(avatar_bytes))

    async def create_ship_image(self, user1_avatar, user2_avatar, percentage):
        background = Image.new('RGB', (1000, 400), (255, 238, 238))
        draw = ImageDraw.Draw(background)
        
        size = (200, 200)
        mask = Image.new('L', size, 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0) + size, fill=255)
        
        avatar1 = ImageOps.fit(user1_avatar, size)
        avatar2 = ImageOps.fit(user2_avatar, size)
        avatar1.putalpha(mask)
        avatar2.putalpha(mask)
        
        background.paste(avatar1, (100, 100), avatar1)
        background.paste(avatar2, (700, 100), avatar2)
        
        try:
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 120)
            except:
                font = ImageFont.load_default()
        
        heart_url = "https://www.iconpacks.net/icons/1/free-heart-icon-431-thumb.png"
        async with aiohttp.ClientSession() as session:
            async with session.get(heart_url) as response:
                heart_bytes = await response.read()
                heart_img = Image.open(BytesIO(heart_bytes))
        
        heart_size = (80, 80)
        heart_img = heart_img.resize(heart_size)

        heart_x = 500 - (heart_size[0] // 2)
        heart_y = 100
        if heart_img.mode == 'RGBA':
            background.paste(heart_img, (heart_x, heart_y), heart_img)
        else:
            background.paste(heart_img, (heart_x, heart_y))
        
        percentage_font = font.font_variant(size=80)
        draw.text((500, 250), f"{percentage}%", fill=(100, 100, 100), font=percentage_font, anchor="mm")
        
        bar_width = 600
        bar_height = 40
        x = (1000 - bar_width) // 2
        y = 300
        
        draw.rectangle([x, y, x + bar_width, y + bar_height], fill=(255, 255, 255), outline=(200, 200, 200))
        
        progress_width = int(bar_width * (percentage / 100))
        draw.rectangle([x, y, x + progress_width, y + bar_height], fill=(255, 150, 150))
        
        img_byte_arr = BytesIO()
        background.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        return img_byte_arr

    @nextcord.slash_command(name="ship", description="Check the compatibility between two users")
    async def ship(self, interaction: nextcord.Interaction, 
                  user1: nextcord.Member = SlashOption(description="The first user to ship", required=True),
                  user2: Optional[nextcord.Member] = SlashOption(description="The second user to ship", required=False)):
        await interaction.response.defer()
        if user2 is None:
            user2 = interaction.user
        ids = sorted([user1.id, user2.id])
        seed = int(str(ids[0]) + str(ids[1]))
        random.seed(seed)
        percentage = random.randint(0, 100)
        avatar1 = await self.get_avatar_image(str(user1.display_avatar.url))
        avatar2 = await self.get_avatar_image(str(user2.display_avatar.url))
        image_bytes = await self.create_ship_image(avatar1, avatar2, percentage)
        embed = nextcord.Embed(title=f"💖 Shipping {user1.name} and {user2.name}!", color=0xff69b4)
        embed.set_image(url="attachment://ship.png")
        file = nextcord.File(fp=image_bytes, filename="ship.png")
        await interaction.followup.send(file=file, embed=embed)


    


def setup(bot):
    bot.add_cog(misc(bot))
    

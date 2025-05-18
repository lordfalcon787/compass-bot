import nextcord
import random
import nextcord.ext.commands
from nextcord.ext import commands, application_checks
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

    @nextcord.slash_command(name="ship", description="Check the compatibility between two users", contexts=[0, 1, 2])
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

    @nextcord.slash_command(name="embed", contexts=[0, 1, 2])
    @application_checks.guild_only()
    async def embed_slash(self, interaction: nextcord.Interaction):
        pass

    @embed_slash.subcommand(name="fetchdescription", description="Fetch the description of an embed")
    @application_checks.guild_only()
    async def fetch_description(self, interaction: nextcord.Interaction, 
                                message_id: str = SlashOption(description="Enter the message ID of the embed to fetch the description of", required=True)):
        await interaction.response.defer(ephemeral=True)
        message = await interaction.channel.fetch_message(int(message_id))
        embed = message.embeds[0]
        await interaction.followup.send(f"```{embed.description}```", ephemeral=True)
    
    @embed_slash.subcommand(name="edit", description="Edit an embed")
    @application_checks.guild_only()
    async def edit_embed(self, interaction: nextcord.Interaction, 
                        message_id: str = SlashOption(description="Enter the message ID of the embed to edit", required=True),
                        title: str = SlashOption(description="Enter a title for the embed", required=False),
                        description: str = SlashOption(description="Enter a description for the embed", required=False),
                        footer: str = SlashOption(description="Enter a footer for the embed", required=False),
                        color: str = SlashOption(description="Enter a color for the embed", required=False),
                        image: str = SlashOption(description="Enter an image url for the embed", required=False),
                        thumbnail: str = SlashOption(description="Enter a thumbnail url for the embed", required=False)):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("You do not have permission to use this command.", ephemeral=True)
            return
        message = await interaction.channel.fetch_message(int(message_id))
        embed = message.embeds[0]
        if title is not None:
            embed.title = title
        if description is not None:
            description = description.replace("\\n", "\n")
            embed.description = description
        if footer is not None:
            embed.set_footer(text=footer)
        if color is not None:
            embed.color = int(color, 16)
        if image is not None:
            embed.set_image(url=image)
        if thumbnail is not None:
            embed.set_thumbnail(url=thumbnail)
        await message.edit(embed=embed)
        await interaction.followup.send("Embed edited.", ephemeral=True)

    @embed_slash.subcommand(name="create", description="Create an embed", contexts=[0, 1, 2])
    @application_checks.guild_only()
    async def embed_slash_create(self, interaction: nextcord.Interaction, 
                   title: str = SlashOption(description="Enter a title for the embed", required=True),
                   description: str = SlashOption(description="Enter a description for the embed", required=True),
                   footer: str = SlashOption(description="Enter a footer for the embed", required=False),
                   color: str = SlashOption(description="Enter a color for the embed", required=False),
                   image: str = SlashOption(description="Enter an image url for the embed", required=False),
                   thumbnail: str = SlashOption(description="Enter a thumbnail url for the embed", required=False)):
        await interaction.response.defer(ephemeral=True)
        description = description.replace("\\n", "\n")
        embed = nextcord.Embed(title=title, description=description)
        if color is not None:
            embed.color = int(color, 16)
        if footer is not None:
            embed.set_footer(text=footer)
        if image is not None:
            embed.set_image(url=image)
        if thumbnail is not None:
            embed.set_thumbnail(url=thumbnail)
        await interaction.channel.send(embed=embed)
        await interaction.followup.send("Embed sent.", ephemeral=True)


    


def setup(bot):
    bot.add_cog(misc(bot))
    

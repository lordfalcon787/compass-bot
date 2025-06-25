import nextcord
from nextcord.ext import commands, application_checks, tasks
from typing import Optional
from nextcord import SlashOption
import asyncio
from utils.mongo_connection import MongoConnection
import aiohttp
from PIL import Image
from io import BytesIO

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["AutoResponder"]
collection2 = db["ARWords"]
misc = db["Misc"]
configuration = db["Configuration"]


class AR(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cache = {}

    def cog_unload(self):
        if self.update_cached_words.is_running():
            self.update_cached_words.cancel()
        if self.check_ar.is_running():
            self.check_ar.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        print("AR cog is ready.")
        if not self.update_cached_words.is_running():
            self.update_cached_words.start()
        if not self.check_ar.is_running():
            self.check_ar.start()

    async def ban_check(interaction: nextcord.Interaction):
        banned_users = misc.find_one({"_id": "bot_banned"})
        if banned_users:
            if str(interaction.user.id) in banned_users:
                embed = nextcord.Embed(title="Bot Banned", description=f"You are banned from using this bot. Please contact the bot owner if you believe this is an error. \n\n **Reason:** {banned_users[str(interaction.user.id)]}", color=16711680)
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return False
            else:
                return True
        else:
            return True
        
    @tasks.loop(minutes=3)
    async def update_cached_words(self):
        doc = collection2.find_one({"_id": "cachedwords"})
        doc.pop("_id")
        self.cache = doc
        
    @tasks.loop(hours=1)
    async def check_ar(self):
        words = list(collection2.find())
        images = [".gif", ".png", ".jpg", ".jpeg", ".webp"]
        mentions = list(collection.find())
        config = configuration.find_one({"_id": "ar_config"})
        allowed = config["allowed"]
        words_allowed = config["words_allowed"]
        link_allowed = config["link_allowed"]
        for doc in words:
            if doc["_id"] == "cachedwords":
                continue
            user = int(doc["_id"])
            doc.pop("_id")
            if len(doc.keys()) == 0:
                collection2.delete_one({"_id": user})
                continue
            for key in doc:
                guild = key.split("_")[1]
                guild = int(guild)
                guild = self.bot.get_guild(guild)
                if guild:
                    member = guild.get_member(user)
                    if member:
                        member_roles = [role.id for role in member.roles]
                        if str(guild.id) in words_allowed:
                            guild_allowed = words_allowed[str(guild.id)]
                            if not any(role in guild_allowed for role in member_roles):
                                if "word" in key:
                                    collection2.update_one({"_id": "cachedwords"}, {"$pull": {str(guild.id): doc[key]}})
                                collection2.update_one({"_id": user}, {"$unset": {key: ""}})
                        else:
                            if "word" in key:
                                collection2.update_one({"_id": "cachedwords"}, {"$pull": {str(guild.id): doc[key]}})
                            collection2.update_one({"_id": user}, {"$unset": {key: ""}})
                    else:
                        if "word" in key:
                            collection2.update_one({"_id": "cachedwords"}, {"$pull": {str(guild.id): doc[key]}})
                        collection2.update_one({"_id": user}, {"$unset": {key: ""}})
                else:
                    if "word" in key:
                        collection2.update_one({"_id": "cachedwords"}, {"$pull": {str(guild.id): doc[key]}})
                    collection2.update_one({"_id": user}, {"$unset": {key: ""}})
        for doc in mentions:
            user = int(doc["_id"])
            doc.pop("_id")
            if len(doc.keys()) == 0:
                collection.delete_one({"_id": user})
                continue
            for key in doc:
                guild = key.split("_")[1]
                guild = int(guild)
                emoji = doc[key]
                guild = self.bot.get_guild(guild)
                image_check = False
                if any(image in emoji for image in images):
                    image_check = True
                if guild:
                    member = guild.get_member(user)
                    if member:
                        member_roles = [role.id for role in member.roles]
                        if not image_check:
                            if str(guild.id) in allowed:
                                guild_allowed = allowed[str(guild.id)]
                                if not any(role in guild_allowed for role in member_roles):
                                    collection.update_one({"_id": user}, {"$unset": {key: ""}})
                        else:
                            if str(guild.id) in link_allowed and str(guild.id) in allowed:
                                guild_allowed = link_allowed[str(guild.id)]
                                guild_allowed_words = allowed[str(guild.id)]
                                if not any(role in guild_allowed for role in member_roles) or not any(role in guild_allowed_words for role in member_roles):
                                    collection.update_one({"_id": user}, {"$unset": {key: ""}})
                            else:
                                collection.update_one({"_id": user}, {"$unset": {key: ""}})
                    else:
                        collection.update_one({"_id": user}, {"$unset": {key: ""}})
                else:
                    collection.update_one({"_id": user}, {"$unset": {key: ""}})

    @nextcord.slash_command(description="Auto responder for mentions and words.", name="ar")
    @application_checks.guild_only()
    async def ar(self, interaction: nextcord.Interaction,
                type: int = SlashOption(description="The type of auto responder to use.", choices={"Mention": 1, "Word": 2}),
                emoji: str = SlashOption(description="The emoji to use for to respond with."),
                word: Optional[str] = SlashOption(description="The word to trigger on if type is word.")):
        TYPE = type
        emojis = []
        guilds = self.bot.guilds
        for guild in guilds:
            extend = [str(emojii) for emojii in guild.emojis]
            emojis.extend(extend)
        if not "<" in emoji:
            emoji = next((e for e in emojis if emoji in e), emoji)
        EMOJI = emoji
        WORD_TYPE = f"Word auto responder is set to reply to \"{word}\" with \n# {EMOJI}" if word is not None else f"Mention auto responder is set to reply with \n# {EMOJI}"


        config = configuration.find_one({"_id": "ar_config"})
        link_allowed = config["link_allowed"]
        words_allowed = config["words_allowed"]
        allowed = config["allowed"]
        guild_id = str(interaction.guild.id)

        if guild_id not in allowed:
            await interaction.response.send_message(content=f"This server does not have auto responder fully configured. Please run `/config` to configure the auto responder.", ephemeral=True)
            return
        
        allowed_roles = allowed[guild_id]
        try:
            words_allowed_roles = words_allowed[guild_id]
        except:
            words_allowed_roles = []
        try:
            link_allowed_roles = link_allowed[guild_id]
        except:
            link_allowed_roles = []

        if word is None and not any(role.id in allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message(content=f"You do not have permission to use this command.", ephemeral=True)
            return
        elif not word is None and not any(role.id in words_allowed_roles for role in interaction.user.roles):
            await interaction.response.send_message(content=f"You do not have permission to use this command.", ephemeral=True)
            return
        elif word is None and TYPE == 2:
            await interaction.response.send_message(content=f"You must provide a word to trigger on if you choose to trigger on a word", ephemeral=True)
            return
        elif not EMOJI in emojis:
            if not any(role.id in link_allowed_roles for role in interaction.user.roles) and not "https://" in EMOJI:
                await interaction.response.send_message(content=f"You must provide a valid emoji which exists in the server.", ephemeral=True)
                return
        elif not word is None:
            if word.lower() not in interaction.user.nick.lower() or word.lower() not in interaction.user.name.lower():
                await interaction.response.send_message(content=f"You must provide a word which is in your display name/username to trigger on.", ephemeral=True)
                return
        elif word is None:
            word = "N/A"

        if not word is None and "https://" in EMOJI:
            await interaction.response.send_message(content=f"You cannot use links for response to a custom trigger.", ephemeral=True)
            return
        
        if word is None and "https://" in EMOJI:
            if not ".gif" in EMOJI and not ".png" in EMOJI and not ".jpg" in EMOJI and not ".jpeg" in EMOJI and not "tenor.com" in EMOJI and not ".webp" in EMOJI:
                await interaction.response.send_message(content=f"Please enter a valid image to use a response.", ephemeral=True)
                return
            
        if "https://" in EMOJI:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(EMOJI) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            image = Image.open(BytesIO(image_data))
                            width, height = image.size
                            if height > width:
                                await interaction.response.send_message(content="Vertical images are not allowed.", ephemeral=True)
                                return
            except Exception as e:
                await interaction.response.send_message(content="Failed to validate image. Please try again.", ephemeral=True)
                return

        
        if TYPE == 1:
            collection.update_one({"_id": interaction.user.id}, {"$set": {f"emoji_{interaction.guild.id}": EMOJI}}, upsert=True)
        elif TYPE == 2:
            wordd = word.lower()
            collection2.update_one({"_id": interaction.user.id}, {"$set": {f"emoji_{interaction.guild.id}": EMOJI, f"word_{interaction.guild.id}": wordd}}, upsert=True)
            collection2.update_one({"_id": "cachedwords"}, {"$addToSet": {f"{interaction.guild.id}": wordd}}, upsert=True)
        
        message = WORD_TYPE
        embed = nextcord.Embed(title="Auto Responder Set", description=message, color=65280)
        embed.set_footer(text=f"Requested by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @nextcord.slash_command(description="Remove an auto responder.")
    @application_checks.guild_only()
    async def removear(self, interaction: nextcord.Interaction,
                       user: nextcord.Member = SlashOption(description="The user to remove the auto responder for."),
                       type: int = SlashOption(description="The type of auto responder to remove.", choices={"Mention": 1, "Word": 2})):
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(content=f"You do not have permission to use this command.", ephemeral=True)
            return
        
        TYPE = type
        try:
            if TYPE == 1:
                collection.update_one({"_id": user.id}, {"$unset": {f"emoji_{interaction.guild.id}": ""}})
            elif TYPE == 2:
                collection2.update_one({"_id": user.id}, {"$unset": {f"emoji_{interaction.guild.id}": "", f"word_{interaction.guild.id}": ""}})
        except:
            await interaction.response.send_message(content=f"Auto responder not found.", ephemeral=True)
            return
        await interaction.response.send_message(content=f"Auto responder removed.", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        try:
            if message.author.bot:
                return
            elif message.mentions:
                asyncio.create_task(self.ar_mentions(message))
                return
            
            cached_words = self.cache.get(str(message.guild.id))
            con = message.content.lower()
            if not cached_words:
                return
            if any(word in con for word in cached_words):
                asyncio.create_task(self.auto_respond(message))
                return
            else:
                return
        except:
            return
        
            
    async def auto_respond(self, message):
        split_message = message.content.split(" ")
        split_message = list(dict.fromkeys(split_message))
        for word in split_message:
            try:
                var = collection2.find_one({f"word_{message.guild.id}": word.lower()})     
                if var:
                    await message.reply(content=f"{var[f'emoji_{message.guild.id}']}", mention_author=False)
            except:
                continue
        return
    
    async def ar_mentions(self, message):
        for user in message.mentions:
            try:
                if user.mention in message.content:
                    var = collection.find_one({"_id": user.id})
                    if var:
                        await message.reply(content=f"{var[f'emoji_{message.guild.id}']}", mention_author=False)
            except:
                continue
        return


def setup(bot: commands.Bot):
    bot.add_cog(AR(bot))
    
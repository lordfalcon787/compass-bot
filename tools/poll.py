import nextcord
from nextcord.ext import commands, application_checks
from nextcord import SlashOption
from typing import Optional
from datetime import datetime, timedelta
import asyncio

RC_ID = 1205270486230110330

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Polls"]
misc = db["Misc"]
configuration = db["Configuration"]

class PollManager:
    def __init__(self):
        self.pending_updates = {}
        self.update_locks = {}
        
    async def update_poll_message(self, message: nextcord.Message):
        poll = collection.find_one({"_id": str(message.id)})
        if not poll:
            return
            
        created_at = datetime.fromtimestamp(message.created_at.timestamp())
        if datetime.now() - created_at < timedelta(hours=1):
            await self._do_update(message, poll)
            return
            
        self.pending_updates[message.id] = (message, poll)
        
        if message.id not in self.update_locks:
            self.update_locks[message.id] = asyncio.Lock()
            asyncio.create_task(self._delayed_update(message.id))
    
    async def _delayed_update(self, message_id):
        async with self.update_locks[message_id]:
            await asyncio.sleep(180)
            
            if message_id in self.pending_updates:
                message, poll = self.pending_updates[message_id]
                latest_poll = collection.find_one({"_id": str(message_id)})
                await self._do_update(message, latest_poll)
                del self.pending_updates[message_id]
                del self.update_locks[message_id]
    
    async def _do_update(self, message: nextcord.Message, poll: dict):
        view = nextcord.ui.View()
        
        for i in range(10):
            choice_key = f"choice_{i}"
            choice_text_key = f"choice_{i}_text"
            if choice_key in poll and choice_text_key in poll:
                votes = len(poll[choice_key])
                choice_text = poll[choice_text_key]
                button = nextcord.ui.Button(
                    style=nextcord.ButtonStyle.primary,
                    label=f"{choice_text} [{votes}]",
                    custom_id=f"poll_choice_{i}"
                )
                view.add_item(button)
        
        try:
            await message.edit(view=view)
        except Exception as e:
            print(f"Failed to update poll {message.id}: {e}")

class BinaryView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.binary_yes = nextcord.ui.Button(label="Yes [0]", style=nextcord.ButtonStyle.success, custom_id="poll_binary_yes")
        self.binary_no = nextcord.ui.Button(label="No [0]", style=nextcord.ButtonStyle.danger, custom_id="poll_binary_no")
        self.binary_yes.callback = self.binary_yes_callback
        self.binary_no.callback = self.binary_no_callback
        self.add_item(self.binary_yes)
        self.add_item(self.binary_no)

    async def binary_yes_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("You are not an admin, you cannot vote on this poll.", ephemeral=True)
            return
        doc = collection.find_one({"_id": str(interaction.message.id)})
        if doc:
            if str(interaction.user.id) in doc["yes"]:
                await interaction.followup.send("You have already voted yes.", ephemeral=True)
                return
            if str(interaction.user.id) in doc["no"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"no": str(interaction.user.id)}})   
            collection.update_one({"_id": str(interaction.message.id)}, {"$push": {"yes": str(interaction.user.id)}})
            embed = nextcord.Embed(title="You have voted yes.", color=65280)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.update_binary_poll_message(interaction.message)
        else:
            await interaction.followup.send("This poll does not exist.", ephemeral=True)

    async def binary_no_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("You are not an admin, you cannot vote on this poll.", ephemeral=True)
            return
        doc = collection.find_one({"_id": str(interaction.message.id)})
        if doc:
            if str(interaction.user.id) in doc["no"]:
                await interaction.followup.send("You have already voted no.", ephemeral=True)
                return
            if str(interaction.user.id) in doc["yes"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"yes": str(interaction.user.id)}})   
            collection.update_one({"_id": str(interaction.message.id)}, {"$push": {"no": str(interaction.user.id)}})
            embed = nextcord.Embed(title="You have voted no.", color=65280)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.update_binary_poll_message(interaction.message)
        else:
            await interaction.followup.send("This poll does not exist.", ephemeral=True)
        

    async def update_binary_poll_message(self, message: nextcord.Message):
        doc = collection.find_one({"_id": str(message.id)})
        if doc:
            yes = len(doc["yes"])
            no = len(doc["no"])
            self.binary_yes.label = f"Yes [{yes}]"
            self.binary_no.label = f"No [{no}]"
            await message.edit(view=self)
        else:
            await message.edit(view=None)

class AdminPollView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        self.yes = nextcord.ui.Button(label="Yes [0]", style=nextcord.ButtonStyle.success, custom_id="poll_yes")
        self.abstain = nextcord.ui.Button(label="Abstain [0]", style=nextcord.ButtonStyle.secondary, custom_id="poll_abstain")
        self.no = nextcord.ui.Button(label="No [0]", style=nextcord.ButtonStyle.danger, custom_id="poll_no")
        self.yes.callback = self.yes_callback
        self.abstain.callback = self.abstain_callback
        self.no.callback = self.no_callback
        self.add_item(self.yes)
        self.add_item(self.abstain)
        self.add_item(self.no)

    async def yes_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("You are not an admin, you cannot vote on this poll.", ephemeral=True)
            return
        doc = collection.find_one({"_id": str(interaction.message.id)})
        if doc:
            if str(interaction.user.id) in doc["yes"]:
                await interaction.followup.send("You have already voted yes.", ephemeral=True)
                return
            if str(interaction.user.id) in doc["no"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"no": str(interaction.user.id)}})   
            if str(interaction.user.id) in doc["abstain"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"abstain": str(interaction.user.id)}})
            collection.update_one({"_id": str(interaction.message.id)}, {"$push": {"yes": str(interaction.user.id)}})
            embed = nextcord.Embed(title="You have voted yes.", color=65280)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.update_admin_poll_message(interaction.message)
        else:
            await interaction.followup.send("This poll does not exist.", ephemeral=True)

    async def abstain_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("You are not an admin, you cannot vote on this poll.", ephemeral=True)
            return
        doc = collection.find_one({"_id": str(interaction.message.id)})
        if doc:
            if str(interaction.user.id) in doc["abstain"]:
                await interaction.followup.send("You have already voted abstain.", ephemeral=True)
                return
            if str(interaction.user.id) in doc["yes"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"yes": str(interaction.user.id)}})   
            if str(interaction.user.id) in doc["no"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"no": str(interaction.user.id)}})
            collection.update_one({"_id": str(interaction.message.id)}, {"$push": {"abstain": str(interaction.user.id)}})
            embed = nextcord.Embed(title="You have voted abstain.", color=65280)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.update_admin_poll_message(interaction.message)
        else:
            await interaction.followup.send("This poll does not exist.", ephemeral=True)

    async def no_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.followup.send("You are not an admin, you cannot vote on this poll.", ephemeral=True)
            return
        doc = collection.find_one({"_id": str(interaction.message.id)})
        if doc:
            if str(interaction.user.id) in doc["no"]:
                await interaction.followup.send("You have already voted no.", ephemeral=True)
                return
            if str(interaction.user.id) in doc["yes"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"yes": str(interaction.user.id)}})   
            if str(interaction.user.id) in doc["abstain"]:
                collection.update_one({"_id": str(interaction.message.id)}, {"$pull": {"abstain": str(interaction.user.id)}})
            collection.update_one({"_id": str(interaction.message.id)}, {"$push": {"no": str(interaction.user.id)}})
            embed = nextcord.Embed(title="You have voted no.", color=65280)
            await interaction.followup.send(embed=embed, ephemeral=True)
            await self.update_admin_poll_message(interaction.message)
        else:
            await interaction.followup.send("This poll does not exist.", ephemeral=True)
        

    async def update_admin_poll_message(self, message: nextcord.Message):
        doc = collection.find_one({"_id": str(message.id)})
        if doc:
            yes = len(doc["yes"])
            abstain = len(doc["abstain"])
            no = len(doc["no"])
            self.yes.label = f"Yes [{yes}]"
            self.no.label = f"No [{no}]"
            self.abstain.label = f"Abstain [{abstain}]"
            await message.edit(view=self)
        else:
            await message.edit(view=None)
        
class Poll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.poll_manager = PollManager()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Poll cog is ready")
        self.bot.add_view(AdminPollView())
        self.bot.add_view(BinaryView())

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
        
    @nextcord.slash_command(name="poll", description="Create a poll with up to 10 choices", contexts=[0, 1, 2], integration_types=[0, 1])
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def poll(self, interaction: nextcord.Interaction):
        pass

    @poll.subcommand(name="admin", description="Create a Robbing Central Admin Poll")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def poll_admin(self, interaction: nextcord.Interaction, title: str = SlashOption(description="The title of the poll"), description: str = SlashOption(description="The description of the poll", required=False), binary: bool = SlashOption(description="Whether the poll is binary", required=False)):
        await interaction.response.defer(ephemeral=True)
        if interaction.guild.id != 1205270486230110330:
            await interaction.send("This command can only be used in the Robbing Central Discord Server.", ephemeral=True)
            return
        admin_role = interaction.guild.get_role(1205270486502867030)
        if admin_role not in interaction.user.roles and interaction.user.id != interaction.guild.owner_id:
            await interaction.send("You do not have permission to use this command.", ephemeral=True)
            return
        embed = nextcord.Embed(title=title, description=description, color=nextcord.Color.blue())
        embed.set_footer(text=f"Admin poll created by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)
        if binary:
            view = BinaryView()
        else:
            view = AdminPollView()
        message = await interaction.channel.send(embed=embed, view=view)
        if binary:
            collection.insert_one({"_id": str(message.id), "title": title, "description": description, "binary": binary, "creator": str(interaction.user.id), "created_at": datetime.utcnow(), "yes": [], "no": []})
        else:
            collection.insert_one({"_id": str(message.id), "title": title, "description": description, "binary": binary, "creator": str(interaction.user.id), "created_at": datetime.utcnow(), "yes": [], "no": [], "abstain": []})
        await interaction.followup.send("Poll created", ephemeral=True)
        
        

    @poll.subcommand(name="end", description="End a poll")
    @application_checks.check(ban_check)
    async def poll_end(self, interaction: nextcord.Interaction, poll_id: str = SlashOption(description="The message ID of the poll to end")):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            await interaction.send("You do not have permission to use this command.", ephemeral=True)
            return
        print("1")
        doc = collection.find_one({"_id": poll_id})
        if not doc:
            await interaction.send("Poll not found", ephemeral=True)
            return
        print("2")
        view = nextcord.ui.View()
        print("3")
        for i in range(10):
            choice_key = f"choice_{i}"
            text_key = f"choice_{i}_text"
            print("4")
            if choice_key not in doc or text_key not in doc:
                continue
            print("5")
            choice_text = doc[text_key]
            choice_votes = len(doc[choice_key])
            print("6")
            button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label=f"{choice_text} [{choice_votes}]", custom_id=f"poll_choice_disabled_{i}", disabled=True)
            print("7")
            view.add_item(button)
        print("8")
        poll_msg = await interaction.channel.fetch_message(poll_id)
        print("9")
        await poll_msg.edit(view=view)
        await interaction.send("Poll ended.", ephemeral=True)

    @poll.subcommand(name="anonymous", description="Create an anonymous poll")
    @application_checks.check(ban_check)
    async def poll_anonymous(
        self,
        interaction: nextcord.Interaction,
        title: str = SlashOption(description="The title of the poll"),
        choice1: str = SlashOption(description="First choice"),
        choice2: str = SlashOption(description="Second choice"),
        description: Optional[str] = SlashOption(description="The description of the poll"),
        image: Optional[nextcord.Attachment] = SlashOption(description="The image to display on the embed."),
        choice3: Optional[str] = SlashOption(description="Third choice", required=False),
        choice4: Optional[str] = SlashOption(description="Fourth choice", required=False),
        choice5: Optional[str] = SlashOption(description="Fifth choice", required=False),
        choice6: Optional[str] = SlashOption(description="Sixth choice", required=False),
        choice7: Optional[str] = SlashOption(description="Seventh choice", required=False),
        choice8: Optional[str] = SlashOption(description="Eighth choice", required=False),
        choice9: Optional[str] = SlashOption(description="Ninth choice", required=False),
        choice10: Optional[str] = SlashOption(description="Tenth choice", required=False),
    ):
        choices = [choice1, choice2, choice3, choice4, choice5, choice6, choice7, choice8, choice9, choice10]
        choices = [choice for choice in choices if choice is not None]

        if interaction.guild is not None:
            config = configuration.find_one({"_id": "config"})
            guild = str(interaction.guild.id)
            poll_role = config["poll_role"]
            if guild in poll_role:
                poll_role = poll_role[guild]
            else:
                poll_role = [11]

            user_roles = [role.id for role in interaction.user.roles]
            bool = False

            for pollrole in poll_role:
                if pollrole in user_roles:
                    bool = True
                    break

            if not interaction.user.guild_permissions.administrator and not bool:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return

        if len(choices) < 2:
            await interaction.response.send_message("You need to provide at least 2 choices for the poll.", ephemeral=True)
            return

        embed = nextcord.Embed(title=title, color=nextcord.Color.blue())
        embed.set_footer(text=f"Poll created by {interaction.user.name} - This poll is anonymous", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        if description:
            description = description.replace("\\n", "\n")
            embed.description = description
        
        if image:
            embed.set_image(url=image.url)

        view = nextcord.ui.View()
        for i, choice in enumerate(choices):
            button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label=f"{choice} [0]", custom_id=f"pollanon_choice_{i}")
            view.add_item(button)

        message2 = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Poll created", ephemeral=True)

        poll_data = {
            "_id": str(message2.id),
            "title": title,
            "creator": str(interaction.user.id),
            "created_at": datetime.utcnow(),
            "voters": []
        }

        for i, choice in enumerate(choices):
            poll_data[f"choice_{i}"] = 0
            poll_data[f"choice_{i}_text"] = choice
        try:
            collection.insert_one(poll_data)
        except Exception as e:
            print(f"Error adding poll to database: {e}")
        

    @poll.subcommand(name="create", description="Create a poll with up to 10 choices")
    @application_checks.check(ban_check)
    async def poll_create(
        self,
        interaction: nextcord.Interaction,
        title: str = SlashOption(description="The title of the poll"),
        choice1: str = SlashOption(description="First choice"),
        choice2: str = SlashOption(description="Second choice"),
        anonymous: Optional[bool] = SlashOption(description="Whether the poll should be anonymous"),
        description: Optional[str] = SlashOption(description="The description of the poll"),
        image: Optional[nextcord.Attachment] = SlashOption(description="The image to display on the embed."),
        choice3: Optional[str] = SlashOption(description="Third choice", required=False),
        choice4: Optional[str] = SlashOption(description="Fourth choice", required=False),
        choice5: Optional[str] = SlashOption(description="Fifth choice", required=False),
        choice6: Optional[str] = SlashOption(description="Sixth choice", required=False),
        choice7: Optional[str] = SlashOption(description="Seventh choice", required=False),
        choice8: Optional[str] = SlashOption(description="Eighth choice", required=False),
        choice9: Optional[str] = SlashOption(description="Ninth choice", required=False),
        choice10: Optional[str] = SlashOption(description="Tenth choice", required=False),
    ):
        choices = [choice1, choice2, choice3, choice4, choice5, choice6, choice7, choice8, choice9, choice10]
        choices = [choice for choice in choices if choice is not None]

        if interaction.guild is not None:
            config = configuration.find_one({"_id": "config"})
            guild = str(interaction.guild.id)
            poll_role = config["poll_role"]
            if guild in poll_role:
                poll_role = poll_role[guild]
            else:
                poll_role = [11]

            user_roles = [role.id for role in interaction.user.roles]
            has_permission = any(pollrole in user_roles for pollrole in poll_role)

            if not interaction.user.guild_permissions.administrator and not has_permission:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return

        if len(choices) < 2:
            await interaction.response.send_message("You need to provide at least 2 choices for the poll.", ephemeral=True)
            return

        embed = nextcord.Embed(title=title, color=nextcord.Color.blue())
        embed.set_footer(text=f"Poll created by {interaction.user.name}", icon_url=interaction.user.avatar.url if interaction.user.avatar else None)

        if description:
            description = description.replace("\\n", "\n")
            embed.description = description
        
        if image:
            embed.set_image(url=image.url)

        if anonymous:
            anon = True
        else:
            anon = False

        

        view = nextcord.ui.View()
        for i, choice in enumerate(choices):
            button = nextcord.ui.Button(style=nextcord.ButtonStyle.primary, label=f"{choice} [0]", custom_id=f"poll_choice_{i}")
            view.add_item(button)

        message2 = await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("Poll created", ephemeral=True)

        poll_data = {
            "_id": str(message2.id),
            "title": title,
            "creator": str(interaction.user.id),
            "created_at": datetime.utcnow(),
            "anonymous": anon
        }

        for i, choice in enumerate(choices):
            poll_data[f"choice_{i}"] = []
            poll_data[f"choice_{i}_text"] = choice
        try:
            collection.insert_one(poll_data)
        except Exception as e:
            print(f"Error adding poll to database: {e}")

    async def anon_choice(self, interaction: nextcord.Interaction):
        custom_id = interaction.data["custom_id"]
        choice_index = int(custom_id.split("_")[-1])
        poll_id = str(interaction.message.id)
        user_id = interaction.user.id
        try:
            await interaction.response.defer(ephemeral=True)
        except:
            pass
        poll = collection.find_one({"_id": poll_id})
        voters = poll["voters"]
        if poll:
            choice_key = f"choice_{choice_index}"
            if choice_key not in poll:
                embed = nextcord.Embed(title="This choice is no longer available.", color=16711680)
                try:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return
            if user_id in voters:
                embed = nextcord.Embed(title="You've already voted for this poll.", color=16711680)
                try:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except:
                    await interaction.followup.send(embed=embed, ephemeral=True)
                return
            voters.append(user_id)
            collection.update_one({"_id": poll_id}, {"$set": {"voters": voters}})
            collection.update_one({"_id": poll_id}, {"$inc": {choice_key: 1}})
            await self.update_anon_poll_message(interaction.message)
            embed = nextcord.Embed(title=f"You've voted for: **{poll[f'choice_{choice_index}_text']}**", color=65280)
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)
        else:
            try:
                embed = nextcord.Embed(title="This poll no longer exists.", color=16711680)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                await interaction.followup.send(embed=embed, ephemeral=True)

    async def update_anon_poll_message(self, message: nextcord.Message):
        poll = collection.find_one({"_id": str(message.id)})
        if poll:
            view = nextcord.ui.View()
            for i in range(10):
                choice_key = f"choice_{i}"
                choice_text_key = f"choice_{i}_text"
                if choice_key in poll and choice_text_key in poll:
                    votes = poll[choice_key]
                    choice_text = poll[choice_text_key]
                    button = nextcord.ui.Button(
                        style=nextcord.ButtonStyle.primary,
                        label=f"{choice_text} [{votes}]",
                        custom_id=f"pollanon_choice_{i}"
                    )
                    view.add_item(button)
            
            await message.edit(view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: nextcord.Interaction):
        if not interaction.type == nextcord.InteractionType.component:
            return
        if interaction.data["component_type"] == 2:
            custom_id = interaction.data["custom_id"]
            if custom_id.startswith("pollanon_choice_"):
                await self.anon_choice(interaction)
            if custom_id.startswith("poll_choice_"):
                try:
                    await interaction.response.defer(ephemeral=True)
                except:
                    pass
                choice_index = int(custom_id.split("_")[-1])
                poll_id = str(interaction.message.id)
                user_id = str(interaction.user.id)

                poll = collection.find_one({"_id": poll_id})
                if poll:
                    choice_key = f"choice_{choice_index}"
                    if choice_key not in poll:
                        embed = nextcord.Embed(title="This choice is no longer available.", color=16711680)
                        try:
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        except:
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        return

                    if user_id not in poll[choice_key]:
                        for i in range(10):
                            other_choice = f"choice_{i}"
                            if other_choice in poll and user_id in poll[other_choice]:
                                collection.update_one(
                                    {"_id": poll_id},
                                    {"$pull": {other_choice: user_id}}
                                )

                        collection.update_one(
                            {"_id": poll_id},
                            {"$addToSet": {choice_key: user_id}}
                        )
                        
                        choice_text = poll.get(f"choice_{choice_index}_text", "Unknown choice")
                        
                        try:
                            embed = nextcord.Embed(title=f"You voted for: {choice_text}", color=65280)
                            embed.set_footer(text="Your vote will be added to the results shortly.")
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        except:
                            await interaction.followup.send(embed=embed, ephemeral=True)
                        
                        await self.poll_manager.update_poll_message(interaction.message)
                    else:
                        try:
                            embed = nextcord.Embed(title="You've already voted for this option.", color=16711680)
                            await interaction.response.send_message(embed=embed, ephemeral=True)
                        except Exception as e:
                            await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    try:
                        embed = nextcord.Embed(title="This poll no longer exists.", color=16711680)
                        await interaction.response.send_message(embed=embed, ephemeral=True)
                    except:
                        await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        try:
            message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        except:
            return
        if not message.embeds:
            return
        elif not message.embeds[0].footer:
            return
        elif not message.embeds[0].footer.text.startswith("Poll created by"):
            return
        elif "anonymous" in message.embeds[0].footer.text:
            await payload.member.send("This poll is anonymous. You are unable to see the results.")
            return
        elif payload.emoji.name != "📊":
            return
        elif not payload.member.guild_permissions.administrator:
            return
        poll_id = str(payload.message_id)

        poll = collection.find_one({"_id": poll_id})
        if poll:
            anon = poll["anonymous"]
            if anon:
                user = await self.bot.fetch_user(payload.user_id)
                if user:
                    try:
                        await user.send("This poll is anonymous. You are unable to see the results.")
                    except nextcord.Forbidden:
                        pass
                await message.clear_reactions()
                return
            
            choice_data = []
            for i in range(10):
                choice_key = f"choice_{i}"
                choice_text_key = f"choice_{i}_text"
                if choice_key in poll and choice_text_key in poll:
                    choice_text = poll[choice_text_key]
                    voters = poll[choice_key]
                    
                    voter_strings = []
                    for voter_id in voters:
                        user = await self.bot.fetch_user(int(voter_id))
                        if user:
                            voter_strings.append(f"`{user.name}` | <@{user.id}>")
                    
                    if voter_strings:
                        choice_data.append((choice_text, voter_strings))

            # Split into pages of 5 choices each
            pages = []
            current_page = nextcord.Embed(title="Poll Results", color=0x00ff00)
            field_count = 0

            for choice_text, voter_strings in choice_data:
                # Split voter strings into chunks of 15 to stay under 1024 chars
                chunks = []
                current_chunk = []
                current_length = 0
                
                for voter in voter_strings:
                    if current_length + len(voter) + 1 > 1000:  # Leave some buffer
                        chunks.append(current_chunk)
                        current_chunk = [voter]
                        current_length = len(voter)
                    else:
                        current_chunk.append(voter)
                        current_length += len(voter) + 1  # +1 for newline
                
                if current_chunk:
                    chunks.append(current_chunk)

                # Add fields for this choice, creating new pages as needed
                for chunk_idx, chunk in enumerate(chunks):
                    value = "\n".join(chunk)
                    name = f"{choice_text}" if chunk_idx == 0 else f"{choice_text} (cont.)"
                    
                    if field_count >= 5:
                        pages.append(current_page)
                        current_page = nextcord.Embed(title="Poll Results", color=0x00ff00)
                        field_count = 0
                    
                    current_page.add_field(name=name, value=value, inline=False)
                    field_count += 1

            if field_count > 0:
                pages.append(current_page)

            # Set footer for all pages
            for i, page in enumerate(pages):
                page.set_footer(text=f"Poll results for {payload.message_id} | Page {i+1}/{len(pages)}", 
                              icon_url=message.embeds[0].footer.icon_url)

            await message.clear_reactions()
            
            user = await self.bot.fetch_user(payload.user_id)
            if user:
                try:
                    if pages:
                        current_page = 0
                        view = nextcord.ui.View(timeout=300)
                        
                        async def previous_callback(interaction: nextcord.Interaction):
                            nonlocal current_page
                            current_page = (current_page - 1) % len(pages)
                            await interaction.response.edit_message(embed=pages[current_page])
                            
                        async def next_callback(interaction: nextcord.Interaction):
                            nonlocal current_page
                            current_page = (current_page + 1) % len(pages)
                            await interaction.response.edit_message(embed=pages[current_page])
                            
                        prev_button = nextcord.ui.Button(label="Previous", style=nextcord.ButtonStyle.gray)
                        next_button = nextcord.ui.Button(label="Next", style=nextcord.ButtonStyle.gray)
                        
                        prev_button.callback = previous_callback
                        next_button.callback = next_callback
                        
                        if len(pages) > 1:
                            view.add_item(prev_button)
                            view.add_item(next_button)
                            
                        await user.send(embed=pages[0], view=view)
                    else:
                        result_embed = nextcord.Embed(title="Poll Results", color=0x00ff00)
                        result_embed.description = "No votes recorded yet"
                        result_embed.set_footer(text=f"Poll results for {payload.message_id}",
                                              icon_url=message.embeds[0].footer.icon_url)
                        await user.send(embed=result_embed)
                except nextcord.Forbidden:
                    pass

def setup(bot):
    bot.add_cog(Poll(bot))
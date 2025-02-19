import nextcord
from nextcord.ext import commands, application_checks
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
misc = db["Misc"]
configuration = db["Configuration"]

class ChangeNameModal(nextcord.ui.Modal):
    def __init__(self, bot):
        super().__init__(
            "Change Name",
            timeout=300,
        )
        self.name = nextcord.ui.TextInput(
            label="New Name",
            placeholder="Enter the new name",
            min_length=1,
            max_length=30,
        )
        self.bot = bot
        self.add_item(self.name)

    async def callback(self, interaction: nextcord.Interaction):
        name = self.name.value
        name = name.replace(" ", "-")
        footer = interaction.message.embeds[0].footer.text
        id = footer.split(" ")[1]
        channel = await self.bot.fetch_channel(int(id))
        try:
            await channel.edit(name=f"➤┊{name}")
        except:
            await interaction.response.send_message("An error occurred while changing the name of the channel. Please contact an administrator if the issue persists.", ephemeral=True)
            return
        try:
            await interaction.response.send_message("Name changed successfully!", ephemeral=True)
        except:
            pass

class AddUserSelect(nextcord.ui.UserSelect):
    def __init__(self, channel, bot):
        super().__init__(
            placeholder="Add Friends",
            min_values=1,
            max_values=5,
        )
        self.channel = channel
        self.bot = bot
    async def callback(self, interaction: nextcord.Interaction):
        users_in_channel = [user_id for user_id, perms in self.channel.overwrites.items() if isinstance(user_id, nextcord.Member) and not user_id.bot and perms.view_channel and user_id != interaction.user]
        if str(interaction.user.id) not in self.channel.topic:
            try:
                await interaction.response.send_message("You are not the owner of this channel!", ephemeral=True)
            except:
                pass
            return
        
        user_roles = [role.id for role in interaction.user.roles]
        doc = configuration.find_one({"_id": "config"})
        pcms_roles = doc["pcms"]
        pcms_reqs = doc["pcms_reqs"]
        guild_id = str(interaction.guild.id)

        if guild_id not in pcms_roles or guild_id not in pcms_reqs:
            try:
                await interaction.response.send_message("PCMS is not configured for this server. Please contact an administrator.", ephemeral=True)
            except:
                pass
            return
        
        members = 0
        if guild_id in pcms_roles:
            guild_roles = pcms_roles[guild_id]
            for role_id in guild_roles:
                if int(role_id) in user_roles:
                    members += guild_roles[role_id]

        if len(self.values) + len(users_in_channel) > members:
            try:
                await interaction.response.send_message("You cannot add this many friends to the channel!", ephemeral=True)
            except:
                pass
            return
        
        for selected_user in self.values:
            if selected_user in users_in_channel:
                pass
            else:
                await self.channel.set_permissions(selected_user, view_channel=True, send_messages=None)
        users_in_channel = [user_id for user_id, perms in self.channel.overwrites.items() if isinstance(user_id, nextcord.Member) and not user_id.bot and perms.view_channel and user_id != interaction.user]
        current_embed = interaction.message.embeds[0]
        friends = [f'<@{user_id.id}>' for user_id in users_in_channel]
        if friends:
            friends_list = "\n".join(friends)
        else:
            friends_list = "None"
        for index, field in enumerate(current_embed.fields):
            if field.name == "Friends":
                current_embed.set_field_at(index, name="Friends", value=friends_list, inline=True)
                break
        await interaction.message.edit(embed=current_embed)
        try:
            await interaction.response.send_message(f"Added {', '.join([user.mention for user in self.values])} to the channel!", ephemeral=True)
        except:
            pass

class RemoveUserSelect(nextcord.ui.UserSelect):
    def __init__(self, channel, bot):
        super().__init__(
            placeholder="Remove Friends",
            min_values=1,
            max_values=5,
        )
        self.channel = channel
        self.bot = bot
    async def callback(self, interaction: nextcord.Interaction):
        users_in_channel = [user_id for user_id, perms in self.channel.overwrites.items() if isinstance(user_id, nextcord.Member) and not user_id.bot and perms.view_channel and user_id != interaction.user]
        if str(interaction.user.id) not in self.channel.topic:
            try:
                await interaction.response.send_message("You are not the owner of this channel!", ephemeral=True)
            except:
                pass
            return
        for selected_user in self.values:
            if selected_user not in users_in_channel:
                pass
            else:
                await self.channel.set_permissions(selected_user, overwrite=None)
        users_in_channel = [user_id for user_id, perms in self.channel.overwrites.items() if isinstance(user_id, nextcord.Member) and not user_id.bot and perms.view_channel and user_id != interaction.user]
        current_embed = interaction.message.embeds[0]
        friends = [f'<@{user_id.id}>' for user_id in users_in_channel]
        if friends:
            friends_list = "\n".join(friends)
        else:
            friends_list = "None"
        for index, field in enumerate(current_embed.fields):
            if field.name == "Friends":
                current_embed.set_field_at(index, name="Friends", value=friends_list, inline=True)
                break
        await interaction.message.edit(embed=current_embed)
        try:
            await interaction.response.send_message(f"Removed {', '.join([user.mention for user in self.values])} from the channel!", ephemeral=True)
        except:
            pass

class AddFriendsView(nextcord.ui.View):
    def __init__(self, channel, bot):
        super().__init__(timeout=60)
        self.channel = channel
        self.bot = bot
        self.add_item(AddUserSelect(channel, bot))
        self.add_item(RemoveUserSelect(channel, bot))
        
        change_name_button = nextcord.ui.Button(label="Change Name", style=nextcord.ButtonStyle.primary)
        change_name_button.callback = self.change_name
        self.add_item(change_name_button)
        
        self.message = None

    async def change_name(self, interaction: nextcord.Interaction):
        interaction_author = self.message.interaction.user
        if interaction_author.id != interaction.user.id:
            try:
                await interaction.response.send_message("You cannot change the name of this channel!", ephemeral=True)
            except:
                pass
            return
        await interaction.response.send_modal(ChangeNameModal(self.bot))

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

class PCMS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("PCMS is ready")

    async def ban_check(interaction: nextcord.Interaction):
        banned_users = misc.find_one({"_id": "bot_banned"})
        if banned_users:
            if str(interaction.user.id) in banned_users:
                embed = nextcord.Embed(title="Bot Banned", description=f"You are banned from using this bot. Please contact the bot owner if you believe this is an error. \n\n **Reason:** {banned_users[str(interaction.user.id)]}", color=16711680)
                try:
                    await interaction.response.send_message(embed=embed, ephemeral=True)
                except:
                    pass
                return False
            else:
                return True
        else:
            return True
        
    @nextcord.slash_command(name="mychannel", description="Manage your private channel.")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def mychannel(self, interaction: nextcord.Interaction):
        try:
            await interaction.response.send_message("This command is deprecated. Please use `/pcms channel` instead.", ephemeral=True)
        except:
            pass
    
    @nextcord.slash_command(name="pcms", description="Manage your private channels.")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def pcms(self, interaction: nextcord.Interaction):
       pass

    @pcms.subcommand(name="channel", description="Manage your private channel.")
    @application_checks.guild_only()
    @application_checks.check(ban_check)
    async def channel(self, interaction: nextcord.Interaction):
        channels = [channel for channel in interaction.guild.channels]
        user_channel = None

        for a_channel in channels:
            if not isinstance(a_channel, nextcord.TextChannel):
                continue
            description = a_channel.topic
            if description is None:
                continue
            if str(interaction.user.id) in description and "channel" in description.lower() and "private" in description.lower():
                user_channel = a_channel
                break
        
        if user_channel is None:
            for a_channel in channels:
                if not isinstance(a_channel, nextcord.TextChannel):
                    continue
                description = a_channel.topic
                if description is None:
                    continue
                if str(interaction.user.id) in description:
                    user_channel = a_channel
                    break

        if user_channel is None:
            embed = nextcord.Embed(description=f"{RED_X} No private channel was found for you, please contact an administrator if you need assistance.")
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
            return
        
        user_roles = [role.id for role in interaction.user.roles]
        doc = configuration.find_one({"_id": "config"})
        pcms_roles = doc["pcms"]
        pcms_reqs = doc["pcms_reqs"]
        guild_id = str(interaction.guild.id)

        if guild_id not in pcms_roles or guild_id not in pcms_reqs:
            embed = nextcord.Embed(description=f"{RED_X} PCMS is not configured for this server. Please contact an administrator.", color=0xFF0000)
            try:
                await interaction.response.send_message(embed=embed, ephemeral=True)
            except:
                pass
            return

        embed = nextcord.Embed(color=0x2b2d31)
        embed.set_author(name=f"Personal Channel Management System", icon_url=interaction.user.display_avatar.url)
        embed.set_footer(text=f"ID: {user_channel.id}")
        embed.add_field(name="Channel", value=f"<#{user_channel.id}>", inline=True)
        embed.add_field(name="Owner", value=f"<@{interaction.user.id}>", inline=True)
        embed.add_field(name="Created At", value=f"<t:{int(user_channel.created_at.timestamp())}:f>", inline=True)

        guild_reqs = pcms_reqs[guild_id]
        req_text = ""
        for role_id in guild_reqs:
            if int(role_id) in user_roles:
                req_text += f"{GREEN_CHECK} {interaction.guild.get_role(int(role_id)).mention}\n"
            else:
                req_text += f"{RED_X} {interaction.guild.get_role(int(role_id)).mention}\n"
        embed.add_field(name="Role Requirements", value=req_text.strip(), inline=True)

        value = ""
        members = 0
        guild_roles = pcms_roles[guild_id]
        for role_id in guild_roles:
            if int(role_id) in user_roles:
                value += f"{GREEN_CHECK} `{guild_roles[role_id]}` {interaction.guild.get_role(int(role_id)).mention}\n"
                members += guild_roles[role_id]
            else:
                value += f"{RED_X} `{guild_roles[role_id]}` {interaction.guild.get_role(int(role_id)).mention}\n"
        value += f"You can add `{members}` total."
        embed.add_field(name="Role Thresholds", value=value, inline=True)

        users_in_channel = [user_id for user_id, perms in user_channel.overwrites.items() if isinstance(user_id, nextcord.Member) and not user_id.bot and perms.view_channel]
        value = ""
        for member in users_in_channel:
            if not member.id == interaction.user.id:
                value = f"{value}\n<@{member.id}>"
        if value == "":
            value = "None"
        embed.add_field(name="Friends", value=value, inline=True)

        view = AddFriendsView(user_channel, self.bot)
        try:
            await interaction.response.send_message(embed=embed, view=view)
        except:
            pass
        view.message = await interaction.original_message()

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.Message):
        if message.author.bot:
            return
        con = message.content.lower()
        if "<@&1205270486263795720>" not in con:
            return
        if message.channel.id != 1334991861185515636 and "1y" not in con and "1 year" not in con and "<#1336149180069969920>" not in con and "1 y" not in con and "master" not in con:
            return
        await message.reply("<@&1209676873949257899> 1 Year Event Detected! This counts towards the masters event! Join up!", mention_author=False)
        if "gartic" not in con and "tea" not in con:
            return
        ice = await self.bot.fetch_user(582702884609851433)
        await ice.send(f"1 Year Event Detected! {message.jump_url}")
            

def setup(bot: commands.Bot):
    bot.add_cog(PCMS(bot))
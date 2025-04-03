import nextcord

from nextcord.ext import commands
from typing import Optional, List
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class Utilv2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Utilityv2 cog is ready.")

    @nextcord.slash_command(name="channel")
    async def channel(self, interaction: nextcord.Interaction):
        pass

    @channel.subcommand(name="create")
    async def create(self, interaction: nextcord.Interaction, name: str, category: Optional[nextcord.CategoryChannel] = None):
        if not interaction.user.guild_permissions.manage_channels:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        try:
            channel = await interaction.guild.create_text_channel(name=name, category=category)
            await interaction.response.send_message(f"Channel created - {channel.mention}.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to create channel.", ephemeral=True)

    @channel.subcommand(name="delete")
    async def delete(self, interaction: nextcord.Interaction, channel: nextcord.TextChannel):
        if not interaction.user.guild_permissions.manage_channels:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_channels:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
        try:
            await channel.delete()
            await interaction.response.send_message(f"Channel deleted.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to delete channel.", ephemeral=True)

    @channel.subcommand(name="rename")
    async def rename(self, interaction: nextcord.Interaction, name: str, channel: Optional[nextcord.TextChannel] = None):
        if channel is None:
            channel = interaction.channel
        if not interaction.user.guild_permissions.manage_channels:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_channels:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
        try:
            await channel.edit(name=name)
            await interaction.response.send_message(f"Channel renamed to {name}.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to rename channel.", ephemeral=True)

    @channel.subcommand(name="viewlock")
    async def viewlock(self, interaction: nextcord.Interaction, access_roles: Optional[List[nextcord.Role]] = None, channel: Optional[nextcord.TextChannel] = None):
        if channel is None:
            channel = interaction.channel
        if not interaction.user.guild_permissions.manage_channels:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_permissions:
                if channel.category:
                    category_perms = channel.category.permissions_for(interaction.user)
                    if not (category_perms.manage_channels or category_perms.manage_permissions):
                        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                    return
        channel_overwrites = channel.overwrites
        if access_roles is not None:
            for role in access_roles:
                channel_overwrites[role] = nextcord.PermissionOverwrite(view_channel=True)  
        channel_overwrites[interaction.guild.default_role] = nextcord.PermissionOverwrite(view_channel=False)
        try:
            await channel.edit(overwrites=channel_overwrites)
            await interaction.response.send_message(f"Channel viewlocked. Only specified roles can view this channel.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Failed to viewlock channel: {str(e)}", ephemeral=True)

    @channel.subcommand(name="unviewlock")
    async def unviewlock(self, interaction: nextcord.Interaction):
        if channel is None:
            channel = interaction.channel
        if not interaction.user.guild_permissions.manage_channels:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_permissions:
                if channel.category:
                    category_perms = channel.category.permissions_for(interaction.user)
                    if not (category_perms.manage_channels or category_perms.manage_permissions):
                        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                        return
                else:
                    await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                    return
        channel_overwrites = channel.overwrites
        channel_overwrites[interaction.guild.default_role] = nextcord.PermissionOverwrite(view_channel=True)
        try:
            await channel.edit(overwrites=channel_overwrites)
            await interaction.response.send_message(f"Channel unviewlocked.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to unviewlock channel.", ephemeral=True)

    @channel.subcommand(name="lock")
    async def lock_channel_slash(self, interaction: nextcord.Interaction, channel: Optional[nextcord.TextChannel] = None):
        if channel is None:
            channel = interaction.channel
        if not interaction.user.guild_permissions.manage_messages:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_messages:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
        try:
            overwrites = channel.overwrites_for(interaction.guild.default_role)
            overwrites.send_messages = False
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
            await interaction.response.send_message(f"Channel locked.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to lock channel.", ephemeral=True)

    @channel.subcommand(name="unlock")
    async def unlock_channel_slash(self, interaction: nextcord.Interaction, channel: Optional[nextcord.TextChannel] = None):
        if channel is None:
            channel = interaction.channel
        if not interaction.user.guild_permissions.manage_messages:
            channel_perms = channel.permissions_for(interaction.user)
            if not channel_perms.manage_messages:
                await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
                return
        try:
            overwrites = channel.overwrites_for(interaction.guild.default_role)
            overwrites.send_messages = None
            await channel.set_permissions(interaction.guild.default_role, overwrite=overwrites)
            await interaction.response.send_message(f"Channel unlocked.", ephemeral=True)
        except:
            await interaction.response.send_message("Failed to unlock channel.", ephemeral=True)

    @commands.command(name="rall", aliases=["removeall"])
    async def removeall(self, ctx):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        guild = str(ctx.guild.id)
        event_manager_role = config["event_manager_role"]
        if guild in event_manager_role:
            event_manager_role = event_manager_role[guild]
        else:
            event_manager_role = 111
        if event_manager_role in user_roles or ctx.author.guild_permissions.administrator:
            pass
        else:
            await ctx.reply("You do not have permission to use this command.", mention_author=False)
            return
        
        player_role = config["player_role"]
        if guild in player_role:
            player_role = player_role[guild]
        else:
            await ctx.reply("The player role is not set. Please set the player role using the `/config` command.", mention_author=False)
            return
        player_role = nextcord.utils.get(ctx.guild.roles, id=player_role)
        embed = nextcord.Embed(title="Confirmation", description=f"{ctx.author.mention}, this command will remove the <@&1205270486246883355> role from all members in the server. Are you sure you want to continue?", color=nextcord.Color.blurple())
        yes_button = nextcord.ui.Button(label="Yes", style=nextcord.ButtonStyle.green)
        no_button = nextcord.ui.Button(label="No", style=nextcord.ButtonStyle.red)
        async def yes_callback(interaction: nextcord.Interaction):
            num = 0
            msg = await interaction.response.send_message("Removing the role from all members. This may take a while, please be patient.")
            await interaction.message.edit(view=None)
            for member in interaction.guild.members:
                if player_role in member.roles:
                    num += 1
                    try:
                        await member.remove_roles(player_role)
                    except:
                        await interaction.channel.send(f"Failed to remove the role from **{member.name}**.")
            await interaction.message.edit(embed=nextcord.Embed(title="Success", description=f"The command has been completed. Removed the role from **{num}** members.", color=nextcord.Color.green()))
            await msg.delete()

        async def no_callback(interaction: nextcord.Interaction):
            await interaction.message.edit(embed=nextcord.Embed(title="Cancelled.", description="The command has been cancelled.", color=nextcord.Color.red()), view=None)
            await interaction.response.defer()
        yes_button.callback = yes_callback
        no_button.callback = no_callback
        view = nextcord.ui.View()
        view.add_item(yes_button)
        view.add_item(no_button)
        await ctx.reply(embed=embed, view=view, mention_author=False)

    async def one_player(self, ctx, split_message, player_role_var):
        player = split_message[1]
        player_role = player_role_var
        if player.isdigit():
            player = int(player)
            player = ctx.guild.get_member(player)
        elif "<@" in player:
            player = player.replace("<@", "").replace(">", "")
            player = int(player)
            player = ctx.guild.get_member(player)
        if not player:
            await ctx.reply("No player with the provided name was found.", mention_author=False)
            return
        if player.id == ctx.author.id:
            await ctx.reply("You cannot modify your own role.", mention_author=False)
            return
        
        player_roles = [role.id for role in player.roles]
        if player_role.id in player_roles:
            try:
                await player.remove_roles(player_role)
                await ctx.reply(f"Removed **{player_role.name}** from **{player.name}**.", mention_author=False)
            except:
                await ctx.reply(f"Failed to remove **{player_role.name}** from **{player.name}**.", mention_author=False)
        else:
            try:
                await player.add_roles(player_role)
                await ctx.reply(f"Added **{player_role.name}** to **{player.name}**.", mention_author=False)
            except:
                await ctx.reply(f"Failed to add **{player_role.name}** to **{player.name}**.", mention_author=False)

    @commands.command(name="p", aliases=["player"])
    async def player(self, ctx):
        user_roles = [role.id for role in ctx.author.roles]
        config = configuration.find_one({"_id": "config"})
        guild = str(ctx.guild.id)
        event_manager_role = config["event_manager_role"]
        if guild in event_manager_role:
            event_manager_role = event_manager_role[guild]
        else:
            event_manager_role = 111

        if event_manager_role in user_roles or ctx.author.guild_permissions.administrator:
            pass
        else:
            await ctx.reply("You do not have permission to use this command.", mention_author=False)
            return
        
        player_role = config["player_role"]
        if guild in player_role:
            player_role = player_role[guild]
        else:
            await ctx.reply("The player role is not set. Please set the player role using the `/config` command.", mention_author=False)
            return
        player_role = nextcord.utils.get(ctx.guild.roles, id=player_role)
        split_message = ctx.message.content.split(" ")
        if ctx.message.reference:
            msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            split_message.append(str(msg.author.id))

        if len(split_message) == 1:
            await ctx.reply("You must provide a player to modify the role for.", mention_author=False)
            return
        elif len(split_message) == 2:
            await self.one_player(ctx, split_message, player_role)
            return
        split_message.pop(0)
        for player in split_message:
            if player.isdigit():
                player = int(player)
                if player == ctx.author.id:
                    continue
                try:
                    player_obj = ctx.guild.get_member(player)
                except:
                    continue
                player_roles = [role.id for role in player_obj.roles]
                if player_role.id in player_roles:
                    await player_obj.remove_roles(player_role)
                    await ctx.reply(f"Removed **{player_role.name}** from **{player_obj.name}**.", mention_author=False)
                else:
                    await player_obj.add_roles(player_role)
                    await ctx.reply(f"Added **{player_role.name}** to **{player_obj.name}**.", mention_author=False)
            elif "<@" in player:
                player = player.replace("<@", "").replace(">", "")
                player = int(player)
                if player == ctx.author.id:
                    continue
                try:
                    player_obj = ctx.guild.get_member(player)
                except:
                    continue
                player_roles = [role.id for role in player_obj.roles]
                if player_role.id in player_roles:
                    await player_obj.remove_roles(player_role)
                    await ctx.reply(f"Removed **{player_role.name}** from **{player_obj.name}**.", mention_author=False)
                else:
                    await player_obj.add_roles(player_role)
                    await ctx.reply(f"Added **{player_role.name}** to **{player_obj.name}**.", mention_author=False)

def setup(bot):
    bot.add_cog(Utilv2(bot))
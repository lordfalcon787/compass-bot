import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
CHANNEL = [1214594429575503912, 1286101587965775953, 1340900373589790780, 1346932927937904743]

from utils.mongo_connection import MongoConnection
mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class Utilv2(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.viewlocked_channels = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("Utilityv2 cog is ready.")

    @nextcord.slash_command(name="viewlock", description="Viewlock a channel.", guild_ids=[1205270486230110330])
    async def viewlock(self, interaction: nextcord.Interaction, role: nextcord.Role = SlashOption(description="The role to viewlock the channel for.")):
        if interaction.channel.id not in CHANNEL:
            await interaction.response.send_message("This command can only be used in events-2, events-3, and mini-games.", ephemeral=True)
            return
        
        user_roles = [role.id for role in interaction.user.roles]
        if 1205270486469058637 in user_roles or interaction.user.guild_permissions.administrator:
            pass
        else:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=False)
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.channel.set_permissions(role, view_channel=True)
        self.viewlocked_channels[interaction.channel.id] = role.id
        await interaction.response.send_message(f"Viewlocked **{interaction.channel.mention}**, so only **{role.mention}** can view the channel.", ephemeral=True)

    @nextcord.slash_command(name="unviewlock", description="Unviewlock a channel.", guild_ids=[1205270486230110330])
    async def unviewlock(self, interaction: nextcord.Interaction):
        if interaction.channel.id not in CHANNEL:
            await interaction.response.send_message("This command can only be used in events-2, events-3, and mini-games.", ephemeral=True)
            return
        
        user_roles = [role.id for role in interaction.user.roles]
        if 1205270486469058637 in user_roles or interaction.user.guild_permissions.administrator:
            pass
        else:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        await interaction.channel.set_permissions(interaction.guild.default_role, view_channel=None)
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        if interaction.channel.id in self.viewlocked_channels:
            role_id = self.viewlocked_channels[interaction.channel.id]
            role = interaction.guild.get_role(role_id)
            if role:
                await interaction.channel.set_permissions(role, overwrite=None)
            del self.viewlocked_channels[interaction.channel.id]
        await interaction.response.send_message(f"Unviewlocked **{interaction.channel.mention}**, so everyone can view the channel.", ephemeral=True)

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
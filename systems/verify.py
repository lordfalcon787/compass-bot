import nextcord
import asyncio

from nextcord.ext import commands
from typing import Optional
from nextcord import SlashOption

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Verification"]

class View(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Verify", style=nextcord.ButtonStyle.green, custom_id="verify")
        button.callback = self.verify_callback
        self.add_item(button)

    async def verify_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.message.id})
        if doc is None:
            embed = nextcord.Embed(title="Error Detected", description="No verification module has been set up in this channel. Please contact a server administrator for more help.", color=nextcord.Color.red())
            await interaction.send(embed=embed, ephemeral=True)
            return
        role = interaction.guild.get_role(doc["role"])
        log = doc.get("log", None)
        if role is None:
            embed = nextcord.Embed(title="Error Detected", description="The role specified in the verification module cannot be found. Please contact a server administrator for more help.", color=nextcord.Color.red())
            await interaction.send(embed=embed, ephemeral=True)
            return
        if role in interaction.user.roles:
            embed = nextcord.Embed(title="Error Detected", description="You already have the role.", color=nextcord.Color.red())
            await interaction.send(embed=embed, ephemeral=True)
            return
        
        embed = nextcord.Embed(title="Verification", description=f"Please click the button below to verify yourself. If you do not respond within 2 minutes, you will be kicked from the server.", color=nextcord.Color.green())
        was_verified = False
        
        async def button_callback(interaction: nextcord.Interaction):
            nonlocal was_verified
            was_verified = True
            await interaction.response.defer(ephemeral=True)
            try:
                await interaction.user.add_roles(role)
            except:
                await interaction.send("An error occurred while adding the role. Please contact a server administrator for more help.", ephemeral=True)
                return
            embed = nextcord.Embed(title="Verification Successful", description="You have been verified.", color=nextcord.Color.green())
            await interaction.message.edit(embed=embed, view=None)
            if log is not None:
                channel = interaction.guild.get_channel(log)
                embed = nextcord.Embed(title=f"{interaction.user.name}'s Verification Status", description=f"**Member:** {interaction.user.name} [{interaction.user.id}]\n**Creation:** {interaction.user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n**Status:** Verified successfully, auto roles added.", color=nextcord.Color.green())
                try:
                    embed.set_thumbnail(url=interaction.user.avatar.url)
                except:
                    pass
                await channel.send(embed=embed)
        
        button = nextcord.ui.Button(label="Verify", style=nextcord.ButtonStyle.green, custom_id="verify")
        button.callback = button_callback
        view = nextcord.ui.View()
        view.add_item(button)
        await interaction.send(embed=embed, view=view, ephemeral=True)
        await asyncio.sleep(120)
        if not was_verified:
           await interaction.guild.kick(interaction.user, reason="Did not verify within 2 minutes.")
        else:
            return
        if log is not None:
            channel = interaction.guild.get_channel(log)
            embed = nextcord.Embed(title=f"{interaction.user.name}'s Verification Status", description=f"**Member:** {interaction.user.name} [{interaction.user.id}]\n**Creation:** {interaction.user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n**Status:** Did not verify within 2 minutes, kicked from server.", color=nextcord.Color.red())
            try:
                embed.set_thumbnail(url=interaction.user.avatar.url)
            except:
                pass
            await channel.send(embed=embed)

class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Verify cog loaded")
        self.bot.add_view(View())

    @nextcord.slash_command(name="verification", description="Setup a verification module in this channel.")
    async def verification(
        self,
        interaction: nextcord.Interaction,
        role: nextcord.Role = SlashOption(description="The role to assign to verified users.", required=True),
        log: Optional[nextcord.TextChannel] = SlashOption(description="The channel to log verification status to.", required=False)
    ):
        await interaction.response.defer(ephemeral=True)
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(title="Error Detected", description="You do not have permission to use this command.", color=nextcord.Color.red())
            await interaction.send(embed=embed, ephemeral=True)
            return
        if not log:
            log = None 
        collection.update_one({"_id": interaction.channel.id}, {"$set": {"role": role.id, "log": log.id if log else None}}, upsert=True)
        embed = nextcord.Embed(title="Verification Module Setup", description="The verification module has been setup in this channel.", color=nextcord.Color.green())
        await interaction.send(embed=embed, ephemeral=True)
        embed = nextcord.Embed(title="Verification Required", description=f"{interaction.guild.name} requires all members to verify themselves before they can interact with the server. Please click the button below to verify yourself.", color=nextcord.Color.blurple())
        view = View()
        await interaction.channel.send(embed=embed, view=view)
    

def setup(bot: commands.Bot):
    bot.add_cog(Verify(bot))

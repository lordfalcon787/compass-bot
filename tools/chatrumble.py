import nextcord
import asyncio
from nextcord.ext import commands
from nextcord import SlashOption
class View(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        accept = nextcord.ui.Button(label="Accept", style=nextcord.ButtonStyle.success, custom_id="accept_callback")
        accept.callback = self.accept_callback
        self.add_item(accept)
        deny = nextcord.ui.Button(label="Deny", style=nextcord.ButtonStyle.danger, custom_id="deny_callback")
        deny.callback = self.deny_callback
        self.add_item(deny)

    async def accept_callback(self, interaction: nextcord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]
        if 1206299567520354317 not in user_roles:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        user = interaction.message.content.split("- ")[1]
        user = user.split(" has")[0]
        user = user.replace("<@", "")
        user = user.replace(">", "")
        user = await self.bot.fetch_user(int(user))
        channel = self.bot.get_channel(1205270487274496054)
        overwrites = channel.overwrites_for(user)
        overwrites.send_messages = True
        overwrites.mention_everyone = True
        overwrites.use_slash_commands = True
        await channel.set_permissions(user, overwrite=overwrites)
        await interaction.response.send_message(content=f"Accepted this chat rumble successfully.", ephemeral=True)
        embed = interaction.message.embeds[0]
        embed.color = nextcord.Color.green()
        await interaction.message.edit(content=f"{interaction.user.mention} has accepted this chat rumble.", view=None, embed=embed)
        try:
            await user.send(content=f"Your chat rumble request has been accepted. All required permissions have been assigned and will be removed automatically after 10 minutes.")
        except:
            await interaction.message.reply(content=f"I was unable to send a message to {user.mention}. Your chat rumble request has been accepted.")
        await asyncio.sleep(900)
        await channel.set_permissions(user, overwrite=None)

    async def deny_callback(self, interaction: nextcord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]
        if 1206299567520354317 not in user_roles:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        user = interaction.message.content.split("- ")[1]
        user = user.split(" has")[0]
        user = user.replace("<@", "")
        user = user.replace(">", "")
        user = await self.bot.fetch_user(int(user))
        await interaction.response.send_message(content=f"Denied this chat rumble successfully.", ephemeral=True)
        await interaction.message.edit(content=f"{interaction.user.mention} has denied this chat rumble.", view=None, color=nextcord.Color.red())
        try:
            await user.send(content=f"Your chat rumble request has been denied, please contact an admin if you believe this was in error.")
        except:
            await interaction.message.reply(content=f"I was unable to send a message to {user.mention}. Your chat rumble request has been denied.")

class ChatRumble(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Chat Rumble cog loaded.")
        self.bot.add_view(View(self.bot))

    

    @nextcord.slash_command(name="chatrumble", description="Request to host a chat rumble.", guild_ids=[1205270486230110330])
    async def chatrumble(self, interaction: nextcord.Interaction,
                         donor: nextcord.Member = SlashOption(description="The donor of the chat rumble."),
                         prize: str = SlashOption(description="The prize for the chat rumble.")):
        user_roles = [role.id for role in interaction.user.roles]
        if 1205270486469058637 not in user_roles:
            await interaction.response.send_message(content="You do not have permission to use this command.", ephemeral=True)
            return
        
        view = View(self.bot)
        embed = nextcord.Embed(title="Chat Rumble Request", color=nextcord.Color.blurple())
        embed.add_field(name="Host", value=interaction.user.mention)
        embed.add_field(name="Donor", value=donor.mention, inline=False)
        embed.add_field(name="Prize", value=prize, inline=False)
        await interaction.response.send_message(content=f"Request sent successfully.")
        await self.bot.get_channel(1304567406890450955).send(content=f"<@&1205270486502867030> <@&1206299567520354317> - {interaction.user.mention} has requested a chat rumble.", embed=embed, view=view)

def setup(bot):
    bot.add_cog(ChatRumble(bot))
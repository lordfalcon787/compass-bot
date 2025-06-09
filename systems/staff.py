import nextcord
import json
from nextcord.ext import commands
import nextcord.ext.commands
from nextcord.ext import commands
from nextcord import SlashOption
from typing import Optional

RC_ID = 1205270486230110330
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"
LOADING = "<a:loading_animation:1218134049780928584>"

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class Use(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        
        button = nextcord.ui.Button(label="Use some.", style=nextcord.ButtonStyle.primary, custom_id="use_some")
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: nextcord.Interaction):
        await interaction.response.send_modal(QuantityModal())


class stafflist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Staff utility cog loaded.")
        self.bot.add_view(Use())

    @commands.command(name="promote")
    async def promote(self, ctx, member: nextcord.Member = None):
        if ctx.guild.id != 1205270486230110330:
            await ctx.send("This command is only available in the Robbing Central server.")
            return
        await ctx.message.add_reaction(LOADING)
        if member is None:
            await ctx.send("Please specify a member to promote.")
            return
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.top_role.position >= ctx.author.top_role.position:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        array = ["★", "✦", "✧", "♢", "GarticMod"]
        roles = member.roles
        new_roles = []
        for role in roles:
            if not any(r for r in array if r in role.name):
                new_roles.append(role)
        removed_roles = len(roles) - len(new_roles)
        retained_roles = len(new_roles) - 1
        if len(new_roles) == len(roles):
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"No dangerous roles to remove were found.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.edit(roles=new_roles)
        except:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"An error occurred while promoting the member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        embed = nextcord.Embed(title = f"Successfully promoted to `Member`", description = f"Flagged and removed `{removed_roles}` roles from {member.mention} with `{retained_roles}` retained.", color=65280)
        await ctx.message.clear_reactions()
        await ctx.reply(embed = embed, mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="modpromote")
    async def modpromote(self, ctx, member: nextcord.Member = None):
        if ctx.guild.id != 1205270486230110330:
            await ctx.send("This command is only available in the Robbing Central server.")
            return
        await ctx.message.add_reaction(LOADING)
        if member is None:
            await ctx.send("Please specify a member to promote.")
            return
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.top_role.position >= ctx.author.top_role.position:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        array = ["Moderator", "Administrator"]
        roles = member.roles
        name_roles = [role.name for role in roles]
        if "✧ Event Manager" not in name_roles:
            await self.promote(ctx, member)
            return
        new_roles = []
        for role in roles:
            if not any(r for r in array if r in role.name):
                new_roles.append(role)
        removed_roles = len(roles) - len(new_roles)
        retained_roles = len(new_roles) - 1
        if len(new_roles) == len(roles):
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"No dangerous roles to remove were found.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.edit(roles=new_roles)
        except:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"An error occurred while promoting the member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        embed = nextcord.Embed(title = f"Successfully promoted to `Member`", description = f"Flagged and removed `{removed_roles}` roles from {member.mention} with `{retained_roles}` retained.", color=65280)
        await ctx.message.clear_reactions()
        await ctx.reply(embed = embed, mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)

    @commands.command(name="emanpromote")
    async def emanpromote(self, ctx, member: nextcord.Member = None):
        if ctx.guild.id != 1205270486230110330:
            await ctx.send("This command is only available in the Robbing Central server.")
            return
        await ctx.message.add_reaction(LOADING)
        if member is None:
            await ctx.send("Please specify a member to promote.")
            return
        if not ctx.author.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.guild_permissions.administrator:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        if member.top_role.position >= ctx.author.top_role.position:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"You do not have permission to promote this member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        array = ["Giveaway Manager", "Event Manager", "GarticMod"]
        roles = member.roles
        name_roles = [role.name for role in roles]
        if "Moderator" not in any(role for role in name_roles):
            await self.promote(ctx, member)
            return
        new_roles = []
        for role in roles:
            if not any(r for r in array if r in role.name):
                new_roles.append(role)
        removed_roles = len(roles) - len(new_roles)
        retained_roles = len(new_roles) - 1
        if len(new_roles) == len(roles):
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"No dangerous roles to remove were found.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        try:
            await member.edit(roles=new_roles)
        except:
            await ctx.message.clear_reactions()
            embed = nextcord.Embed(title = "Promotion Failed", description = f"An error occurred while promoting the member.", color=16711680)
            await ctx.reply(embed = embed, mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        embed = nextcord.Embed(title = f"Successfully promoted to `Member`", description = f"Flagged and removed `{removed_roles}` roles from {member.mention} with `{retained_roles}` retained.", color=65280)
        await ctx.message.clear_reactions()
        await ctx.reply(embed = embed, mention_author=False)
        await ctx.message.add_reaction(GREEN_CHECK)
            
    @commands.command(name="kstaff")
    async def kstaff(self, ctx):
        if ctx.guild.id != 1205270486230110330:
            await ctx.send("This command is only available in the Robbing Central server.")
            return
        role = ctx.guild.get_role(1209039929372315670)
        current_time = int(nextcord.utils.utcnow().timestamp())
        embed = nextcord.Embed(title = "Staff List", description = f"The Robbing Central and all its activities are made possible by the [donations](https://discord.com/channels/1205270486230110330/1205270487454974055) of our members and the dedication of our staff committed to creating a place to stay. This is a list of all our Karuta Managers as of <t:{current_time}:f>.", color = 65280)
        if role:
            members = []
            for member in role.members:
                members.append(f"`{member.name}` | {member.mention}")
            if members:
                embed.add_field(name=role.name, value="\n".join(members), inline=False)
            else:
                embed.add_field(name=role.name, value="No members", inline=False)
        embed.set_footer(text = f"Username | Mention")
        await ctx.reply(embed = embed, mention_author=False)

    @nextcord.slash_command(name="createpc", guild_ids=[RC_ID], description="Create a private channel.")
    async def createpc(self, interaction: nextcord.Interaction, name: str = SlashOption(description="The name of the channel."), user: nextcord.Member = SlashOption(description="The user to create the channel for.")):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        category = interaction.guild.get_channel(1260993149161967646)
        if not category:
            await interaction.response.send_message("The specified category does not exist.", ephemeral=True)
            return
        name = name.replace(" ", "-")
        name = f"➤┊{name}"
        channel = await interaction.guild.create_text_channel(name, category=category)
        await channel.set_permissions(user, view_channel=True)
        await channel.edit(topic=f"Private channel of {user.mention}.")
        await interaction.response.send_message(f"Created {channel.mention}. Mention Copy/Paste: `{channel.mention}`", ephemeral=True)

    @commands.command(name="staff")
    async def stafflist(self, ctx):
        try:
            if ctx.guild.id == 1205270486230110330:
                await self.rc_staff_list(ctx)
                return
            
            config = configuration.find_one({"_id": "config"})["staff_list_roles"]
            guild = str(ctx.guild.id)
            if guild not in config:
                await ctx.send("This server does not have a staff list configured. Please contact an administrator if you believe this is an error.")
                return
            
            staff_roles = config[guild]
            roles = []
            for role_id in staff_roles:
                role = ctx.guild.get_role(int(role_id))
                if role:
                    roles.append(role)
            
            roles.sort(key=lambda x: x.position, reverse=True)

            current_time = int(nextcord.utils.utcnow().timestamp())
            embed = nextcord.Embed(title="Staff List", description=f"This is a list of all our staff as of <t:{current_time}:f>.", color=65280)
            
            added_members = set()
            for role in roles:
                members = []
                for member in role.members:
                    if member.id not in added_members:
                        members.append(f"`{member.name}` | {member.mention}")
                        added_members.add(member.id)
                if members:
                    embed.add_field(name=role.name, value="\n".join(members), inline=False)

            embed.set_footer(text=f"Username | Mention - Total Staff: {len(added_members)}")
            await ctx.reply(embed=embed, mention_author=False)
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    async def rc_staff_list(self, ctx):
        staff_roles = {
            "1366838238056288286": "Head Administrator",
            "1205270486519517204": "Server Head",
            "1205270486502867030": "Administrator",
            "1205270486490292251": "Head Moderator",
            "1205270486490292246": "Moderator",
            "1205270486469058636": "Trial Moderator",
            "1205270486469058637": "Event Manager",
            "1213612442756583494": "Edible Item"
        }
        current_time = int(nextcord.utils.utcnow().timestamp())
        embed = nextcord.Embed(title = "Staff List", description = f"The Robbing Central and all its activities are made possible by the [donations](https://discord.com/channels/1205270486230110330/1205270487454974055) of our members and the dedication of our staff committed to creating a place to stay. This is a list of all our staff as of <t:{current_time}:f>.", color = 65280)
        guild = ctx.guild
        added_members = set()
        owner = guild.owner
        embed.add_field(name="Owner", value=f"`{owner.name}` | <@{owner.id}>", inline=False)
        for role_id, role_name in staff_roles.items():
            role = guild.get_role(int(role_id))
            if role:
                members = []
                for member in role.members:
                    if member.id not in added_members or member.id == 939307545019969536:
                        members.append(f"`{member.name}` | {member.mention}")
                        added_members.add(member.id)
                if members:
                    embed.add_field(name=role_name, value="\n".join(members), inline=False)
        embed.set_footer(text = f"Username | Mention - Total Staff: {len(added_members)}")
        await ctx.send(embed = embed)

    @nextcord.slash_command(guild_ids=[RC_ID], description="Add coins/items to the staff pool for staff members to use.")
    async def staffpool(self, interaction: nextcord.Interaction,
            user: nextcord.Member = SlashOption(description="The user to add to the staff pool."),
            quantity: str = SlashOption(description="The quantity of the staff pool."),
            item: Optional[str] = SlashOption(description="The item to add to the staff pool.")):
        
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        if item is None:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = quantity.lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await interaction.response.send_message("Invalid quantity format. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await interaction.response.send_message("Invalid quantity. Please enter a number.", ephemeral=True)
                    return
            quantity = int(quantity)
            DESC = f"┊ :gift: ┊ **Donor:** {user.mention} \n┊ :money_with_wings: ┊ **Quantity:** {quantity:,} coins"
        else:
            quantity = int(quantity)
            DESC = f"┊ :gift: ┊ **Donor:** {user.mention} \n┊ :money_with_wings: ┊ **Quantity:** {quantity} {item} \n ┊ :small_red_triangle: ┊ **Last Updated By:** {interaction.user.mention}"
        STAFF_POOL_CHANNEL = self.bot.get_channel(1269778241661698089)
        
        embed = nextcord.Embed(title = "Staff Pool Donation",description=DESC, color=0x00ff00)
        view = Use()
        embed.set_thumbnail(url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        embed.set_footer(text=f"", icon_url="https://cdn.discordapp.com/icons/1205270486230110330/f746bd8ccde4545818b80133872adc4e.webp?size=1024&format=webp&width=0&height=512")
        
        await STAFF_POOL_CHANNEL.send(content=f"<@{user.id}> has donated to the staff pool", embed=embed, view=view)
        
        await interaction.response.send_message(f"Added to the staff pool.", ephemeral=True)

class QuantityModal(nextcord.ui.Modal):
    def __init__(self):
        super().__init__(
            "Remaining Quantity",
            timeout=300,
        )

        self.quantity = nextcord.ui.TextInput(
            label="How much is left?",
            min_length=1,
            max_length=20,
            required=True,
            placeholder="If item, enter remaining QUANTITY of items."
        )
        self.add_item(self.quantity)

    async def callback(self, interaction: nextcord.Interaction):
        remaining_quantity = self.quantity.value
        remaining_quantity = remaining_quantity.split(" ")[0]
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        quantity = remaining_quantity.lower()
        if quantity[-1] in multipliers:
            try:
                numeric_part = float(quantity[:-1])
                multiplier = multipliers[quantity[-1]]
                quantity = int(numeric_part * multiplier)
            except ValueError:
                await interaction.response.send_message("Invalid quantity format. Please use a number followed by k, m, b, or t.", ephemeral=True)
                return
        else:
            if ',' in quantity:
                quantity = quantity.replace(',', '')
            try:
                quantity = int(quantity)
            except ValueError:
                await interaction.response.send_message("Invalid quantity. Please enter a number.", ephemeral=True)
                return

        remaining_quantity = quantity
        original_message = interaction.message
        embed = original_message.embeds[0]
        description = embed.description.split('\n')
        for i, line in enumerate(description):
            if '┊ :money_with_wings: ┊ **Quantity:**' in line:
                line = line.replace("┊ :money_with_wings: ┊ **Quantity:** ", "")
                if 'coins' in line:
                    description[i] = f"┊ :money_with_wings: ┊ **Quantity:** {remaining_quantity:,} coins"
                else:
                    split_line = line.split(" ")
                    item = split_line[1:]
                    item_name = ' '.join(item)
                    for it in item:
                        original = it 
                        it = it.replace(",", "")
                        if it.isdigit():
                            item_name = item_name.replace(f"{original} ", "")
                            item_name = item_name.replace(original, "")
                    description[i] = f"┊ :money_with_wings: ┊ **Quantity:** {remaining_quantity:,} {item_name}"
                break
        
        if remaining_quantity <= 0:
            embed.title = "Completed"
            embed.color = nextcord.Color.green()
            await original_message.edit(embed=embed, view=None)
            await original_message.delete(delay=43200)
        else:
            embed.description = '\n'.join(description)
            await original_message.edit(embed=embed)
        for i, line in enumerate(description):
            if '┊ :small_red_triangle: ┊ **Last Updated By:**' in line:
                description[i] = f"┊ :small_red_triangle: ┊ **Last Updated By:** {interaction.user.mention}"
                break
        else:
            description.append(f"┊ :small_red_triangle: ┊ **Last Updated By:** {interaction.user.mention}")

        embed.description = '\n'.join(description)
        await original_message.edit(embed=embed)

        await interaction.response.send_message(f"Updated remaining quantity to {remaining_quantity:,}.", ephemeral=True)

def setup(bot):
    bot.add_cog(stafflist(bot))
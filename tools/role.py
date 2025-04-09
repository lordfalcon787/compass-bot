import nextcord
import asyncio

from nextcord.ext import commands
from typing import Optional
from nextcord import SlashOption
from fuzzywuzzy import process, fuzz
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

class View(nextcord.ui.View):
    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)
        button = nextcord.ui.Button(label="Members with Role", style=nextcord.ButtonStyle.primary)
        button.callback = self.members_with_role
        self.add_item(button)

    async def members_with_role(self, interaction):
        id = interaction.message.embeds[0].footer.text.split(" ")[1]
        role = interaction.guild.get_role(int(id))
        members = role.members
        items_per_page = 20
        total_pages = (len(members) + items_per_page - 1) // items_per_page
        current_page = 1
        
        def get_page_content(page):
            start_idx = (page - 1) * items_per_page
            end_idx = start_idx + items_per_page
            page_members = members[start_idx:end_idx]
            
            content = f"**Members with {role.name}** (Page {page}/{total_pages})\n\n"
            for member in page_members:
                content += f"`{member.name}` | {member.mention}\n"
            return content

        view = nextcord.ui.View(timeout=180)
        
        prev_button = nextcord.ui.Button(label="Previous", style=nextcord.ButtonStyle.secondary, disabled=True)
        next_button = nextcord.ui.Button(label="Next", style=nextcord.ButtonStyle.secondary, disabled=total_pages <= 1)
        
        async def prev_callback(button_interaction):
            nonlocal current_page
            if current_page > 1:
                current_page -= 1
                prev_button.disabled = current_page == 1
                next_button.disabled = False
                content = get_page_content(current_page)
                await button_interaction.response.edit_message(content=content, view=view)
                
        async def next_callback(button_interaction):
            nonlocal current_page
            if current_page < total_pages:
                current_page += 1
                next_button.disabled = current_page == total_pages
                prev_button.disabled = False
                content = get_page_content(current_page)
                await button_interaction.response.edit_message(content=content, view=view)
        
        prev_button.callback = prev_callback
        next_button.callback = next_callback
        
        view.add_item(prev_button)
        view.add_item(next_button)
        
        initial_content = get_page_content(current_page)
        await interaction.response.send_message(content=initial_content, view=view, ephemeral=True)
    
class Role(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Role cog is ready")

    @commands.command(name="deletedusers")
    async def deletedusers(self, ctx):
        guild_members = ctx.guild.members
        deleted_users = []
        for member in guild_members:
            if "deleted_user" in member.name:
                deleted_users.append(member)
        await ctx.send(f"Found {len(deleted_users)} deleted users in the server.")
    
    @nextcord.slash_command(name="customrole", description="Edit your custom role parameters.", guild_ids=[1205270486230110330])
    async def customrole(self, interaction: nextcord.Interaction,
                         name: Optional[str] = SlashOption(description="The new name of the role.", required=False),
                         color: Optional[str] = SlashOption(description="The new color of the role.", required=False),
                         image_icon: Optional[nextcord.Attachment] = SlashOption(description="The new icon of the role.", required=False),
                         emoji_icon: Optional[str] = SlashOption(description="The new emoji icon of the role.", required=False)):
        custom_roles = [role for role in interaction.guild.roles if role.position < interaction.guild.get_role(1216541713489723452).position and role.position > interaction.guild.get_role(1215914992352628858).position]
        member = interaction.guild.get_member(interaction.user.id)
        custom_role = None
        for role in custom_roles:
            if len(role.members) != 1:
                continue
            if member in role.members:
                custom_role = role
                break
        if custom_role is None:
            await interaction.response.send_message("You do not have a custom role or a custom role has not been found.", ephemeral=True)
            return
        things_edited = []
        try:
            role_kwargs = {}
            if name:
                role_kwargs["name"] = name
                things_edited.append("name")
            if color:
                try:
                    role_kwargs["color"] = int(color.replace('#', ''), 16)
                    things_edited.append("color")
                except ValueError:
                    await interaction.response.send_message("Invalid color hex code. Please provide a valid hex color code starting with #.", ephemeral=True)
                    return

            await custom_role.edit(**role_kwargs)

            if image_icon:
                if image_icon.size > 2 * 1024 * 1024:
                    await interaction.response.send_message("The icon file must be under 2MB in size.", ephemeral=True)
                    return
                if not any(image_icon.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    await interaction.response.send_message("The icon file must be a PNG, JPG, or GIF image.", ephemeral=True)
                    return
                icon_bytes = await image_icon.read()
                await custom_role.edit(icon=icon_bytes)
                things_edited.append("icon")
            if emoji_icon:
                try:
                    emoji_id = emoji_icon.split(":")[2].split(">")[0]
                    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
                    await custom_role.edit(icon=url)
                    things_edited.append("emoji icon")
                except Exception as e:
                    await interaction.response.send_message(f"Failed to set emoji as role icon: {str(e)}", ephemeral=True)
                    return
            await interaction.response.send_message(f"Successfully edited role {custom_role.mention}. Changed: {', '.join(things_edited)}", ephemeral=True)
        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to edit roles.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while editing the role: {str(e)}", ephemeral=True)

    @commands.command(name="role")
    async def role(self, ctx):
        split = ctx.message.content.split(" ")
        if len(split) == 1:
            return
        
        if split[1] == "info":
            await self.role_info(ctx)
            return
        
        if len(split) < 3:
            await ctx.send("Please provide a role name. Usage: `-role [user[ [role name/id]`")
        else:
            await self.role_add_remove(ctx, split)
            return
        
    async def role_add_remove(self, ctx, split):
        config = configuration.find_one({"_id": "config"})
        config = config["role_cmd_access_roles"]
        guild = str(ctx.guild.id)
        roles = [role.id for role in ctx.author.roles]
        access_role = 1

        if guild in config:
            access_role = config[guild]

        if not ctx.author.guild_permissions.manage_roles and access_role not in roles:
            await ctx.reply(content="You do not have permission to use this command.", mention_author=False)
            return

        user = split[1]
        user = user.replace("@", "").replace("<", "").replace(">", "")
        role_name = " ".join(split[2:])
        role_name = role_name.replace("<@&", "").replace(">", "")
        try:
            member = ctx.guild.get_member(int(user))
            user = await self.bot.fetch_user(int(user))
        except:
            await ctx.reply(content="User not found.", mention_author=False)
            return
        
        member_roles = [role.id for role in member.roles]
        
        if role_name.strip().isdigit():
            role = ctx.guild.get_role(int(role_name))
        else:
            role_name_lower = role_name
            guild_roles = [role.name for role in ctx.guild.roles]
            role = process.extractOne(role_name_lower, guild_roles, scorer=fuzz.ratio)
            role = nextcord.utils.get(ctx.guild.roles, name=role[0])
           
        if role is None:
            await ctx.reply(content="Role not found.", mention_author=False)
            return

        restricted_permissions = [
            "manage_guild", "manage_roles", "administrator", "manage_messages"
        ]
        if any(getattr(role.permissions, perm) for perm in restricted_permissions):
            await ctx.reply(content="You cannot add or remove roles that have dangerous permissions. This is a safety feature to prevent the bot from being quarantined or as a tool for abuse.", mention_author=False)
            return
        
        if role.position >= ctx.author.top_role.position:
            await ctx.reply(content="You cannot add or remove roles that are above or the same rank as your highest role.", mention_author=False)
            return
        
        type = "Added"
        action = "to"
        if role.id in member_roles:
            try:
                await member.remove_roles(role)
                type = "Removed"
                action = "from"
            except:
                await ctx.reply(content="I do not have permission to remove this role.", mention_author=False)
                return
        else:
            try:
                await member.add_roles(role)
            except:
                await ctx.reply(content="I do not have permission to add this role.", mention_author=False)
                return

        await ctx.reply(content=f"{type} **{role.name}** {action} **{user.name}**", mention_author=False)

    async def role_info(self, ctx):
        if len(ctx.message.content.split(" ")) == 2:
            await ctx.send("Please provide a role name. Usage: `-role info [role name]`")
            return
        role_name = ctx.message.content.replace("role info ", "")
        role_name = role_name.replace("!", "").replace("-", "").replace(".", "")
        if role_name.isdigit():
            role = ctx.guild.get_role(int(role_name))
        else:
            role = next((r for r in ctx.guild.roles if r.name.replace("★ ", "").replace("♢ ", "").lower() == role_name.lower()), None)
        if role is None:
            role = next((r for r in ctx.guild.roles if role_name.lower() in r.name.replace("★ ", "").replace("♢ ", "").lower()), None)
        if role is None:
            await ctx.send(f"Role '{role_name}' not found.")
            return
        
        members_with_role = len(role.members)
        
        embed = nextcord.Embed(title=f"Role Information", color=role.color)
        description = f"""
        **Name:** {role.name}
        **Members:** {members_with_role}
        **Color:** #{role.color.value:06x}
        **Created On:** <t:{int(role.created_at.timestamp())}:F>
        **Displayed Separately:** {role.hoist}
        **Permissions:** {', '.join(' '.join(word.capitalize() for word in perm.replace('_', ' ').split()) for perm, value in role.permissions if value) if any(value for _, value in role.permissions) else 'None'}
        """
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        embed.description = description
        embed.set_footer(text=f"ID: {role.id}")
        try:
            await ctx.reply(embed=embed, mention_author=False, view=View())
        except Exception as e:
            print(e)

    @nextcord.slash_command(name="role", description="Role command")
    async def role_slash(self, interaction: nextcord.Interaction):
        pass

    @role_slash.subcommand(name="delete", description="Delete a role.")
    async def delete(self, interaction: nextcord.Interaction, role: nextcord.Role = SlashOption(description="The role to delete", required=True)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        await role.delete()
        await interaction.send(content=f"Role `{role.name}` has been deleted.", ephemeral=True)

    @role_slash.subcommand(name="in", description="Add a role to users in a role.")
    async def in_(self, interaction: nextcord.Interaction, role: nextcord.Role = SlashOption(description="The role to add to users in", required=True), in_role: nextcord.Role = SlashOption(description="The role that has the users to add the role to", required=True)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if role.position >= interaction.user.top_role.position:
            await interaction.response.send_message("You cannot add a role that is higher than or the same rank as your highest role.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        await interaction.send(content=f"Adding role `{role.name}` to users in role `{in_role.name}`", ephemeral=False)
        added = 0
        total_added = 0
        for member in in_role.members:
            if added == 10:
                await asyncio.sleep(5)
                await interaction.edit_original_message(content=f"Added to {total_added}/{len(in_role.members)} members")
                added = 0
            await member.add_roles(role)
            added += 1
            total_added += 1
        await interaction.send(content=f"Added role `{role.name}` to {len(in_role.members)} users in role `{in_role.name}`", ephemeral=False)

    @role_slash.subcommand(name="edit", description="Easily edit parameters of a role.")
    async def edit(self, interaction: nextcord.Interaction,
                          role: nextcord.Role = SlashOption(description="The role to edit."),
                          name: Optional[str] = SlashOption(description="The new name of the role.", required=False),
                          color: Optional[str] = SlashOption(description="The new color of the role.", required=False),
                          image_icon: Optional[nextcord.Attachment] = SlashOption(description="The new icon of the role.", required=False),
                          emoji_icon: Optional[str] = SlashOption(description="The new emoji icon of the role.", required=False)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        if role.position >= interaction.user.top_role.position:
            await interaction.response.send_message("You cannot edit a role that is higher than or equal to your highest role.", ephemeral=True)
            return
        things_edited = []
        try:
            role_kwargs = {}
            if name:
                role_kwargs["name"] = name
                things_edited.append("name")
            if color:
                try:
                    role_kwargs["color"] = int(color.replace('#', ''), 16)
                    things_edited.append("color")
                except ValueError:
                    await interaction.response.send_message("Invalid color hex code. Please provide a valid hex color code starting with #.", ephemeral=True)
                    return

            await role.edit(**role_kwargs)

            if image_icon:
                if image_icon.size > 2 * 1024 * 1024:
                    await interaction.response.send_message("The icon file must be under 2MB in size.", ephemeral=True)
                    return
                if not any(image_icon.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    await interaction.response.send_message("The icon file must be a PNG, JPG, or GIF image.", ephemeral=True)
                    return
                icon_bytes = await image_icon.read()
                await role.edit(icon=icon_bytes)
                things_edited.append("icon")
            if emoji_icon:
                try:
                    emoji_id = emoji_icon.split(":")[2].split(">")[0]
                    url = f"https://cdn.discordapp.com/emojis/{emoji_id}.png"
                    await role.edit(icon=url)
                    things_edited.append("emoji icon")
                except Exception as e:
                    await interaction.response.send_message(f"Failed to set emoji as role icon: {str(e)}", ephemeral=True)
                    return
            await interaction.response.send_message(f"Successfully edited role {role.mention}. Changed: {', '.join(things_edited)}", ephemeral=True)

        except nextcord.Forbidden:
            await interaction.response.send_message("I don't have permission to edit roles.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred while editing the role: {str(e)}", ephemeral=True)

    @role_slash.subcommand(name="create", description="Create a role.")
    async def create(self, interaction: nextcord.Interaction, name: str = SlashOption(description="The name of the role", required=True), color: Optional[str] = SlashOption(description="The color of the role", required=False), hoist: Optional[bool] = SlashOption(description="Whether the role should be displayed separately", required=False, default=False), mentionable: Optional[bool] = SlashOption(description="Whether the role should be mentionable", required=False, default=False)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        role = await interaction.guild.create_role(name=name)
        if color:
            try:
                await role.edit(color=int(color.replace("#", ""), 16))
            except:
                await interaction.send(content=f"Invalid color hex code. Please provide a valid hex color code starting with #.", ephemeral=True)
                return
        if hoist:
            await role.edit(hoist=hoist)
        if mentionable:
            await role.edit(mentionable=mentionable)
        embed = nextcord.Embed(title=f"Role Created", description=f"Role `{name}` has been created.\n**Name:** {name}\n**Color:** #{role.color.value:06x}\n**Hoist:** {hoist}\n**Mentionable:** {mentionable}", color=role.color)
        embed.color = role.color
        embed.set_footer(text=f"ID: {role.id}")
        await interaction.send(embed=embed, ephemeral=False)

    @role_slash.subcommand(name="remove", description="Remove a role(s) from a member in the server")
    async def remove(self, interaction: nextcord.Interaction, member: nextcord.Member = SlashOption(description="The member to remove the role from", required=True), roles: str = SlashOption(description="The role(s) ID/mention to remove from the member", required=True)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if role.position >= interaction.user.top_role.position:
            await interaction.send(content="You cannot remove a role that is higher than or the same rank as your highest role.", ephemeral=True)
            return
        roles = roles.replace("<@&", "").replace(">", "")
        roles = roles.split(" ")
        for role in roles:
            role = interaction.guild.get_role(int(role))
            if not role:
                await interaction.send(content=f"Role `{role}` not found", ephemeral=True)
                return
            await member.remove_roles(role)
        await interaction.send(content=f"Removed roles from {member.mention}", ephemeral=True)

    @role_slash.subcommand(name="add", description="Add a role(s) to a member in the server")
    async def add(self, interaction: nextcord.Interaction, member: nextcord.Member = SlashOption(description="The member to add the role to", required=True), roles: str = SlashOption(description="The role(s) ID/mention to add to the member", required=True)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=True)
        if role.position >= interaction.user.top_role.position:
            await interaction.send(content="You cannot add a role that is higher than or the same rank as your highest role.", ephemeral=True)
            return
        roles = roles.replace("<@&", "").replace(">", "")
        roles = roles.split(" ")
        for role in roles:
            role = interaction.guild.get_role(int(role))
            if not role:
                await interaction.send(content=f"Role `{role}` not found", ephemeral=True)
                return
            await member.add_roles(role)
        await interaction.send(content=f"Added roles to {member.mention}", ephemeral=True)

    @role_slash.subcommand(name="all", description="Add a role(s) to all members in the server")
    async def all(self, interaction: nextcord.Interaction, role: nextcord.Role = SlashOption(description="The role to add to all members in the server", required=True), bots: Optional[bool] = SlashOption(description="Whether to add the role to bots", required=False, default=False)):
        if not interaction.user.guild_permissions.manage_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        await interaction.response.defer(ephemeral=False)
        if role.position >= interaction.user.top_role.position:
            await interaction.send(content="You cannot add a role that is higher than or the same rank as your highest role.", ephemeral=True)
            return
        if not bots:
            bots = False
        await interaction.send(content=f"Adding role `{role.name}` to all members in the server", ephemeral=False)
        members = interaction.guild.members
        added = 0
        total_added = 0
        for member in members:
                if added == 10:
                    await asyncio.sleep(5)
                    await interaction.edit_original_message(content=f"Added to {total_added}/{len(members)} members")
                    added = 0
                if not bots and member.bot:
                    continue
                await member.add_roles(role)
                added += 1
                total_added += 1
        await interaction.edit_original_message(content=f"Added {total_added} role `{role.name}` to all members in the server")

    @role_slash.subcommand(name="info", description="Get role info")
    async def info(self, interaction: nextcord.Interaction, role: nextcord.Role):
        members_with_role = len(role.members)
        
        embed = nextcord.Embed(title=f"Role Information", color=role.color)
        description = f"**Name:** {role.name}\n**Members:** {members_with_role}\n**Color:** #{role.color.value:06x}\n**Created On:** <t:{int(role.created_at.timestamp())}:F>\n**Displayed Separately:** {role.hoist}\n**Permissions:** {', '.join(' '.join(word.capitalize() for word in perm.replace('_', ' ').split()) for perm, value in role.permissions if value) if any(value for _, value in role.permissions) else 'None'}"
        if role.icon:
            try:
                embed.set_thumbnail(url=role.icon.url)
            except:
                pass
        embed.description = description
        embed.set_footer(text=f"ID: {role.id}")

        await interaction.response.send_message(embed=embed, view=View())

def setup(bot):
    bot.add_cog(Role(bot))
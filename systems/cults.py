import nextcord
from typing import List
from nextcord import SlashOption
from nextcord.ext import commands, tasks
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Cults"]

user_access_ids = [821285989007228928]
role_access_ids = [1375928800046616766]

class Cults(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cults cog loaded")
        self.update_cult_list_message.start()

    @tasks.loop(hours=1)
    async def update_cult_list_message(self):
        doc_1 = collection.find_one({"_id": "cult_list_message"})
        if not doc_1:
            return
        doc_2 = collection.find_one({"_id": "cult_list"})
        points = collection.find_one({"_id": "cult_points"})
        if not doc_2:
            return
        guild = self.bot.get_guild(1205270486230110330)
        channel = guild.get_channel(doc_1["channel"])
        message = await channel.fetch_message(doc_1["msg"])
        if not channel or not message:
            return
        embed = nextcord.Embed(title="Cult List")
        for cult in doc_2:
            if cult == "_id":
                continue
            cult_name = cult
            cult_role = f"<@&{doc_2[cult]['role']}>" if "role" in doc_2[cult] else "None"
            cult_members_str = ", ".join([f"<@{member}>" for member in doc_2[cult]["members"]])
            owner = f"<@{doc_2[cult]['owner']}>" if "owner" in doc_2[cult] else "None"
            total_points = 0
            for member in doc_2[cult]["members"]:
                try:
                    total_points += points[str(member)]["points"]
                except:
                    pass
            embed.add_field(name=f"{cult_name}", value=f"**Role:** {cult_role}\n**Owner:** {owner}\n**Total Points:** {total_points}\n**Members:**{cult_members_str}\n\n", inline=False)
        embed.set_footer(text="Robbing Central Cults", icon_url=guild.icon.url)
        embed.color = 16776960
        await message.edit(embed=embed)

    @nextcord.slash_command(name="cult", description="Cults", guild_ids=[1205270486230110330])
    async def cult(self, interaction: nextcord.Interaction):
        pass

    @cult.subcommand(name="create", description="Create a new cult")
    async def create(self, interaction: nextcord.Interaction, cult_name: str, role: nextcord.Role = SlashOption(description="The role to assign to the cult.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if cult_name in collection.find_one({"_id": "cult_list"}):
            await interaction.response.send_message("That cult already exists.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$set": {cult_name: {"members": [], "role": role.id}}}, upsert=True)
        await interaction.response.send_message(f"Cult `{cult_name}` created successfully.", ephemeral=False)

    @cult.subcommand(name="resetpoints", description="Reset points for everyone.")
    async def resetpoints(self, interaction: nextcord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_points"})
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if not doc:
            await interaction.response.send_message("No cult points data found.", ephemeral=False)
            return
        update_dict = {}
        for user_id, data in doc.items():
            if user_id == "_id":
                continue
            update_dict[f"{user_id}.points"] = 0
        if update_dict:
            collection.update_one({"_id": "cult_points"}, {"$set": update_dict})
            await interaction.response.send_message("All cult points have been reset to 0.", ephemeral=False)
        else:
            await interaction.response.send_message("No users found to reset points for.", ephemeral=False)

    @cult.subcommand(name="role", description="Set the role for a cult")
    async def role(self, interaction: nextcord.Interaction, cult: str = SlashOption(description="The cult to set the role for.", autocomplete=True), role: nextcord.Role = SlashOption(description="The role to assign to the cult.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$set": {f"{cult}.role": role.id}})
        await interaction.response.send_message(f"Role for cult `{cult}` set to {role.mention}.", ephemeral=False)
    
    @cult.subcommand(name="assign", description="Assign user to a cult")
    async def assign(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to assign the user to.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        if cult not in doc:
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        if user.id in doc[cult]["members"]:
            await interaction.response.send_message("That user is already in that cult.", ephemeral=False)
            return
        members_count = len(doc[cult]["members"])
        if members_count >= 10:
            await interaction.response.send_message("That cult has reached the maximum number of members.", ephemeral=False)
            return
        all_members = [member for cult_data in doc.values() if isinstance(cult_data, dict) and "members" in cult_data for member in cult_data["members"]]
        if user.id in all_members:
            await interaction.response.send_message("That user is already in a cult, please remove them from that cult first.", ephemeral=False)
            return
        try:
            await user.add_roles(interaction.guild.get_role(doc[cult]["role"]))
        except:
            await interaction.response.send_message("Failed to add cult role to user.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$push": {f"{cult}.members": user.id}})
        collection.update_one({"_id": "cult_points"}, {"$set": {f"{user.id}.cult": cult}})
        await interaction.response.send_message(f"User {user.mention} assigned to cult `{cult}`.", ephemeral=False)

    @cult.subcommand(name="deassign", description="Remove a user from a cult")
    async def deassign(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to remove the user from.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        doc2 = collection.find_one({"_id": "cult_points"})
        if cult not in doc:
            if cult not in doc2[str(user.id)]["cult"]:
                await interaction.response.send_message("That cult does not exist.", ephemeral=False)
                return
            else:
                collection.update_one({"_id": "cult_points"}, {"$unset": {f"{user.id}.cult": ""}})
                await interaction.response.send_message(f"User {user.mention} removed from cult {cult}.", ephemeral=False)
                return

        is_owner = False
        if "owner" in doc[cult] and doc[cult]["owner"] == user.id:
            is_owner = True
            collection.update_one({"_id": "cult_list"}, {"$unset": {f"{cult}.owner": ""}})

        try:
            collection.update_one({"_id": "cult_list"}, {"$pull": {f"{cult}.members": user.id}})
        except:
            pass
        try:
            collection.update_one({"_id": "cult_points"}, {"$unset": {f"{user.id}.cult": ""}})
        except:
            pass
        try:
            await user.remove_roles(interaction.guild.get_role(doc[cult]["role"]))
        except:
            pass
        if is_owner:
            await interaction.response.send_message(f"User {user.mention} removed from cult `{cult}`. (They were the owner, so the cult now has no owner.)", ephemeral=False)
        else:
            await interaction.response.send_message(f"User {user.mention} removed from cult `{cult}`.", ephemeral=False)
    
    @cult.subcommand(name="view", description="View a cult's members and statistics.")
    async def view(self, interaction: nextcord.Interaction, cult: str = SlashOption(description="The cult to view.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        if cult not in doc:
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        members = doc[cult]["members"]
        members_str = ", ".join([f"<@{member}>" for member in members])
        points = 0
        cult_points = collection.find_one({"_id": "cult_points"})
        for member in members:
            try:
                points += cult_points[str(member)]["points"]
            except:
                pass
        role = f"<@&{doc[cult]['role']}>" if "role" in doc[cult] else "None"
        owner = f"<@{doc[cult]['owner']}>" if "owner" in doc[cult] else "None"
        cult_size = len(doc[cult]["members"])
        embed = nextcord.Embed(title=f"Cult {cult}", description=f"**Role:** {role}\n**Owner:** {owner}\n**Members [{cult_size}/10]:** {members_str}\n**Total Points:** {points}")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @cult.subcommand(name="list", description="View a list of all cults.")
    async def list(self, interaction: nextcord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        points = collection.find_one({"_id": "cult_points"})
        if not doc:
            await interaction.response.send_message("No cults found.", ephemeral=False)
            return
        embed = nextcord.Embed(title="Cult List")
        for cult in doc:
            if cult == "_id":
                continue
            cult_name = cult
            cult_role = f"<@&{doc[cult]['role']}>" if "role" in doc[cult] else "None"
            owner = f"<@{doc[cult]['owner']}>" if "owner" in doc[cult] else "None"
            cult_members_str = ", ".join([f"<@{member}>" for member in doc[cult]["members"]])
            total_points = 0
            for member in doc[cult]["members"]:
                try:
                    total_points += points[str(member)]["points"]
                except:
                    pass
            embed.add_field(name=f"{cult_name}", value=f"**Role:** {cult_role}\n**Owner:** {owner}\n**Total Points:** {total_points}\n**Members:**{cult_members_str}\n\n", inline=False)
        embed.set_footer(text="Robbing Central Cults", icon_url=interaction.guild.icon.url)
        embed.color = 16776960
        await interaction.response.send_message("Sent cult list to channel.", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        collection.update_one({"_id": "cult_list_message"}, {"$set": {f"msg": msg.id, "channel": interaction.channel.id}}, upsert=True)

    @cult.subcommand(name="delete", description="Delete a cult")
    async def delete(self, interaction: nextcord.Interaction, cult: str = SlashOption(description="The cult to delete.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if cult not in collection.find_one({"_id": "cult_list"}):
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$unset": {cult: ""}})
        await interaction.response.send_message(f"Cult {cult} deleted successfully.", ephemeral=False)

    @cult.subcommand(name="setowner", description="Set the owner of a cult")
    async def setowner(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to set the owner of.", autocomplete=True)):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        if cult not in doc:
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        if user.id not in doc[cult]["members"]:
            await interaction.response.send_message("That user is not in that cult, please assign them to the cult first.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$set": {f"{cult}.owner": user.id}})
        await interaction.response.send_message(f"Owner of cult `{cult}` set to {user.mention}.", ephemeral=False)

    @cult.subcommand(name="add", description="Add points to a user.")
    async def add(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if user not in interaction.guild.members:
            await interaction.response.send_message("That user is not in the server.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_points"}, {"$inc": {f"{user.id}.points": amount}})
        await interaction.response.send_message(f"Added `{amount}` points to {user.mention}.", ephemeral=False)

    @cult.subcommand(name="setpoints", description="Set points for a user.")
    async def setpoints(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_points"}, {"$set": {f"{user.id}.points": amount}})
        await interaction.response.send_message(f"Set `{amount}` points for {user.mention}.", ephemeral=False)
    
    @cult.subcommand(name="remove", description="Remove points from a user.")
    async def remove(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        user_roles = [role.id for role in interaction.user.roles]
        if interaction.user.id not in user_access_ids and not interaction.user.guild_permissions.administrator and not any(role_id in user_roles for role_id in role_access_ids):
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if user not in interaction.guild.members:
            await interaction.response.send_message("That user is not in the server.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_points"}, {"$inc": {f"{user.id}.points": -amount}})
        await interaction.response.send_message(f"Removed `{amount}` points from {user.mention}.", ephemeral=False)

    @cult.subcommand(name="leaderboard", description="View the cult leaderboard.")
    async def leaderboard(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": "cult_list"})
        cult_points = collection.find_one({"_id": "cult_points"})
        if not doc or not cult_points:
            await interaction.response.send_message("No cults or points data found.", ephemeral=True)
            return

        leaderboard = []
        for cult_name, cult_data in doc.items():
            if cult_name == "_id":
                continue
            members = cult_data.get("members", [])
            total_points = 0
            for member_id in members:
                user_points = cult_points.get(str(member_id), {}).get("points", 0)
                total_points += user_points
            leaderboard.append((cult_name, total_points))

        leaderboard.sort(key=lambda x: x[1], reverse=True)

        if leaderboard:
            desc = "\n".join([f"{i+1}. `{cult_name}` | {points} Points" for i, (cult_name, points) in enumerate(leaderboard)])
        else:
            desc = "No cults found."

        embed = nextcord.Embed(
            title="Cult Leaderboard",
            description=desc
        )
        embed.color = 16776960
        embed.set_footer(text="Robbing Central Cults", icon_url=interaction.guild.icon.url)
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @cult.subcommand(name="userleaderboard", description="View the user leaderboard.")
    async def userleaderboard(self, interaction: nextcord.Interaction):
        doc = collection.find_one({"_id": "cult_points"})
        if not doc:
            await interaction.response.send_message("No cult points data found.", ephemeral=True)
            return
        user_points = {k: v for k, v in doc.items() if k != "_id" and isinstance(v, dict) and "points" in v}
        sorted_points = sorted(user_points.items(), key=lambda x: x[1]["points"], reverse=True)
        
        if not sorted_points:
            await interaction.response.send_message("No user points data found.", ephemeral=True)
            return

        from nextcord.ui import View, Button

        class LeaderboardView(View):
            def __init__(self, sorted_points, page=0):
                super().__init__(timeout=120)
                self.sorted_points = sorted_points
                self.page = page
                self.max_page = (len(sorted_points) - 1) // 10
                self.update_buttons()

            def update_buttons(self):
                self.clear_items()
                prev_button = Button(label="Previous", style=nextcord.ButtonStyle.primary, disabled=self.page == 0)
                next_button = Button(label="Next", style=nextcord.ButtonStyle.primary, disabled=self.page == self.max_page)
                prev_button.callback = self.prev_page
                next_button.callback = self.next_page
                self.add_item(prev_button)
                self.add_item(next_button)

            async def prev_page(self, interaction: nextcord.Interaction):
                if self.page > 0:
                    self.page -= 1
                    await self.update_embed(interaction)

            async def next_page(self, interaction: nextcord.Interaction):
                if self.page < self.max_page:
                    self.page += 1
                    await self.update_embed(interaction)

            async def update_embed(self, interaction):
                start = self.page * 10
                end = start + 10
                page_points = self.sorted_points[start:end]
                embed = nextcord.Embed(
                    title=f"Cult User Leaderboard (Page {self.page+1}/{self.max_page+1})",
                    description="\n".join([f"{i+1+start}. <@{member}> - {points['points']}" for i, (member, points) in enumerate(page_points)])
                )
                embed.color = 16776960
                embed.set_footer(text=f"Page {self.page+1}/{self.max_page+1}", icon_url=interaction.guild.icon.url)
                self.update_buttons()
                await interaction.response.edit_message(embed=embed, view=self)

        start = 0
        end = 10
        page_points = sorted_points[start:end]
        max_pages = (len(sorted_points) - 1) // 10 + 1
        embed = nextcord.Embed(
            title=f"Cult User Leaderboard (Page 1/{max_pages})",
            description="\n".join([f"{i+1}. <@{member}> - {points['points']}" for i, (member, points) in enumerate(page_points)])
        )
        embed.set_footer(text=f"Page 1/{max_pages}", icon_url=interaction.guild.icon.url)
        embed.color = 16776960
        view = LeaderboardView(sorted_points)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=False)

    @assign.on_autocomplete("cult")
    @deassign.on_autocomplete("cult")
    @setowner.on_autocomplete("cult")
    @view.on_autocomplete("cult")
    @role.on_autocomplete("cult")
    @delete.on_autocomplete("cult")
    async def cult_autocomplete(self, interaction: nextcord.Interaction, current: str):
        try:
            choices = await self.get_choices(interaction, current)
            await interaction.response.send_autocomplete(choices)
        except:
            try:
                await interaction.response.send_autocomplete([])
            except:
                pass

    async def get_choices(self, interaction, current: str) -> List[str]:
        cult_list_doc = collection.find_one({"_id": "cult_list"})
        if not cult_list_doc:
            return []
        cult_names = [key for key in cult_list_doc.keys() if key != "_id"]
        filtered = [name for name in cult_names if name.lower().startswith(current.lower())]
        if not filtered:
            filtered = [name for name in cult_names if current.lower() in name.lower()]
        return filtered[:25]

def setup(bot):
    bot.add_cog(Cults(bot))
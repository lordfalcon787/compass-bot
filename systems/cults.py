import nextcord
from typing import List
from nextcord import SlashOption
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Cults"]

class Cults(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cults cog loaded")

    @nextcord.slash_command(name="cult", description="Cults", guild_ids=[1205270486230110330])
    async def cult(self, interaction: nextcord.Interaction):
        pass

    @cult.subcommand(name="create", description="Create a new cult")
    async def create(self, interaction: nextcord.Interaction, cult_name: str):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if cult_name in collection.find_one({"_id": "cult_list"}):
            await interaction.response.send_message("That cult already exists.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$set": {cult_name: {"members": []}}}, upsert=True)
        await interaction.response.send_message(f"Cult {cult_name} created successfully.", ephemeral=False)
    
    @cult.subcommand(name="assign", description="Assign user to a cult")
    async def assign(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to assign the user to.", autocomplete=True)):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        doc = collection.find_one({"_id": "cult_list"})
        if cult not in doc:
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        if user.id in doc[cult]["members"]:
            await interaction.response.send_message("That user is already in that cult.", ephemeral=False)
            return
        all_members = [member for cult_data in doc.values() if isinstance(cult_data, dict) and "members" in cult_data for member in cult_data["members"]]
        if user.id in all_members:
            await interaction.response.send_message("That user is already in a cult, please remove them from that cult first.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$push": {f"{cult}.members": user.id}})
        collection.update_one({"_id": "cult_points"}, {"$set": {f"{user.id}.cult": cult}})
        await interaction.response.send_message(f"User {user.mention} assigned to cult {cult}.", ephemeral=False)

    @cult.subcommand(name="deassign", description="Remove a user from a cult")
    async def deassign(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to remove the user from.", autocomplete=True)):
        if not interaction.user.guild_permissions.administrator:
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
        try:
            collection.update_one({"_id": "cult_list"}, {"$pull": {f"{cult}.members": user.id}})
        except:
            pass
        try:
            collection.update_one({"_id": "cult_points"}, {"$unset": {f"{user.id}.cult": ""}})
        except:
            pass
        await interaction.response.send_message(f"User {user.mention} removed from cult {cult}.", ephemeral=False)
    
    @cult.subcommand(name="view", description="View a cult's members and statistics.")
    async def view(self, interaction: nextcord.Interaction, cult: str = SlashOption(description="The cult to view.", autocomplete=True)):
        if not interaction.user.guild_permissions.administrator:
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
        embed = nextcord.Embed(title=f"Cult {cult}", description=f"**Owner:** <@{doc[cult]['owner']}>\n**Members:** {members_str}\n**Total Points:** {points}")
        await interaction.response.send_message(embed=embed, ephemeral=False)

    @cult.subcommand(name="delete", description="Delete a cult")
    async def delete(self, interaction: nextcord.Interaction, cult: str = SlashOption(description="The cult to delete.", autocomplete=True)):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if cult not in collection.find_one({"_id": "cult_list"}):
            await interaction.response.send_message("That cult does not exist.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_list"}, {"$unset": {cult: ""}})
        await interaction.response.send_message(f"Cult {cult} deleted successfully.", ephemeral=False)

    @cult.subcommand(name="setowner", description="Set the owner of a cult")
    async def setowner(self, interaction: nextcord.Interaction, user: nextcord.Member, cult: str = SlashOption(description="The cult to set the owner of.", autocomplete=True)):
        if not interaction.user.guild_permissions.administrator:
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
        await interaction.response.send_message(f"Owner of cult {cult} set to {user.mention}.", ephemeral=False)

    @cult.subcommand(name="add", description="Add points to a user.")
    async def add(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if user not in interaction.guild.members:
            await interaction.response.send_message("That user is not in the server.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_points"}, {"$inc": {f"{user.id}.points": amount}})
        await interaction.response.send_message(f"Added {amount} points to {user.mention}.", ephemeral=False)
    
    @cult.subcommand(name="remove", description="Remove points from a user.")
    async def remove(self, interaction: nextcord.Interaction, user: nextcord.Member, amount: int):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=False)
            return
        if user not in interaction.guild.members:
            await interaction.response.send_message("That user is not in the server.", ephemeral=False)
            return
        collection.update_one({"_id": "cult_points"}, {"$inc": {f"{user.id}.points": -amount}})
        await interaction.response.send_message(f"Removed {amount} points from {user.mention}.", ephemeral=False)

    @cult.subcommand(name="leaderboard", description="View the cult leaderboard.")
    async def leaderboard(self, interaction: nextcord.Interaction):
        pass

    @cult.subcommand(name="userleaderboard", description="View the user leaderboard.")
    async def userleaderboard(self, interaction: nextcord.Interaction):
        pass

    @assign.on_autocomplete("cult")
    @deassign.on_autocomplete("cult")
    @view.on_autocomplete("cult")
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
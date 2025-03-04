import nextcord
import asyncio
import random
from nextcord import SlashOption
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["One Of A Kind"]

class NumbersView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button_1 = nextcord.ui.Button(label="1", style=nextcord.ButtonStyle.blurple)
        button_1.callback = self.button_callback_1
        self.add_item(button_1)
        button_2 = nextcord.ui.Button(label="2", style=nextcord.ButtonStyle.blurple)
        button_2.callback = self.button_callback_2
        self.add_item(button_2)
        button_3 = nextcord.ui.Button(label="3", style=nextcord.ButtonStyle.blurple)
        button_3.callback = self.button_callback_3
        self.add_item(button_3)
        button_4 = nextcord.ui.Button(label="4", style=nextcord.ButtonStyle.blurple)
        button_4.callback = self.button_callback_4
        self.add_item(button_4)
        button_5 = nextcord.ui.Button(label="5", style=nextcord.ButtonStyle.blurple)
        button_5.callback = self.button_callback_5
        self.add_item(button_5)

    async def button_callback_1(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id not in doc["players"]:
            await interaction.send("You have not joined the game.", ephemeral=True)
            return
        doc[str(interaction.user.id)] = "1"
        collection.update_one({"_id": interaction.channel.id}, {"$set": doc})
        await interaction.send(f"You have chosen 1.", ephemeral=True)     

    async def button_callback_2(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id not in doc["players"]:
            await interaction.send("You have not joined the game.", ephemeral=True)
            return
        doc[str(interaction.user.id)] = "2"
        collection.update_one({"_id": interaction.channel.id}, {"$set": doc})
        await interaction.send(f"You have chosen 2.", ephemeral=True)
    
    async def button_callback_3(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id not in doc["players"]:
            await interaction.send("You have not joined the game.", ephemeral=True)
            return
        doc[str(interaction.user.id)] = "3"
        collection.update_one({"_id": interaction.channel.id}, {"$set": doc})
        await interaction.send(f"You have chosen 3.", ephemeral=True)
    
    async def button_callback_4(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id not in doc["players"]:
            await interaction.send("You have not joined the game.", ephemeral=True)
            return
        doc[str(interaction.user.id)] = "4"
        collection.update_one({"_id": interaction.channel.id}, {"$set": doc})
        await interaction.send(f"You have chosen 4.", ephemeral=True)

    async def button_callback_5(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id not in doc["players"]:
            await interaction.send("You have not joined the game.", ephemeral=True)
            return
        doc[str(interaction.user.id)] = "5"
        collection.update_one({"_id": interaction.channel.id}, {"$set": doc})
        await interaction.send(f"You have chosen 5.", ephemeral=True)     
    
class JoinView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Join", style=nextcord.ButtonStyle.blurple)
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        current_players = doc["players"]
        if not doc:
            await interaction.send("One of a Kind game not found in this channel.", ephemeral=True)
            return
        if interaction.user.id in current_players:
            await interaction.send("You have already joined the game.", ephemeral=True)
            return
        current_players.append(interaction.user.id)
        collection.update_one({"_id": interaction.channel.id}, {"$set": {"players": current_players}})
        await interaction.send("You have joined the game.", ephemeral=True)

class OneOfAKind(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("One of a Kind Cog loaded")

    @nextcord.slash_command(name="oneofakind", description="Start the One of a Kind game.")
    async def oneofakind(self, interaction: nextcord.Interaction, player_role: nextcord.Role = SlashOption(description="The role to assign to players participating in the game")):
        doc = collection.find_one({"_id": interaction.channel.id})
        if doc:
            button = nextcord.ui.Button(label="Override", style=nextcord.ButtonStyle.danger)
            async def button_callback(interaction: nextcord.Interaction):
                collection.delete_one({"_id": interaction.channel.id})
                await interaction.response.send_message("One of a Kind game overridden in this channel.")
            button.callback = button_callback
            view = nextcord.ui.View()
            view.add_item(button)
            await interaction.response.send_message("One of a Kind game already started in this channel.", view=view)
            return
        collection.insert_one({"_id": interaction.channel.id, "players": []})
        embed = nextcord.Embed(title="One of a Kind", description="This a new event, so please follow the rules and guidelines provided below.\n\nFive players will be selected. Each one of those players can choose a number between 1 and 5. If another player chooses the same number, they will both be eliminated. The person with the lowest __unique__ number will be the winner. The prize will be based on the number the winner chose - e.g., the winner chose 2, so the prize will be 2 of item chosen by the player. \n\nTo join the game, please click the button below.")
        embed.set_footer(text="You have 90 seconds to join the game.", icon_url=self.bot.user.avatar.url)
        view = JoinView()
        await interaction.response.defer(ephemeral=True)
        msg = await interaction.channel.send(embed=embed, view=view)
        await asyncio.sleep(90)
        await msg.edit(view=None)
        doc = collection.find_one({"_id": interaction.channel.id})
        if not doc:
            return
        players = doc["players"]
        if len(players) < 5:
            await interaction.channel.send("The game did not reach 5 players in time. Please try again.")
            collection.delete_one({"_id": interaction.channel.id})
            return
        players = random.sample(players, 5)
        for player in players:
            member = interaction.guild.get_member(player)
            try:
                member.add_roles(player_role)
            except:
                pass
        player_mentions = [f"<@{player}>" for player in players]
        await msg.reply(f"{' '.join(player_mentions)} - the game has started! Please choose a number between 1 and 5. You have 2 minutes to choose a number and discuss with the other players.")
        embed = nextcord.Embed(title="One of a Kind", description="This a new event, so please follow the rules and guidelines provided below.\n\nFive players will be selected. Each one of those players can choose a number between 1 and 5. If another player chooses the same number, they will both be eliminated. The person with the lowest __unique__ number will be the winner. The prize will be based on the number the winner chose - e.g., the winner chose 2, so the prize will be 2 of item chosen by the player.")
        embed.set_footer(text="You have 2 minutes to choose a number and discuss with the other players.")
        view = NumbersView()
        await msg.edit(embed=embed, view=view)
        await asyncio.sleep(120)
        await msg.edit(view=None)
        doc = collection.find_one({"_id": interaction.channel.id})
        players = doc["players"]
        descp = ""
        for player in players:
            if str(player) in doc:
                descp == f"{descp}\n<@{player}>'s Choice: `{doc[str(player)]}`"
            else:
                descp == f"{descp}\n<@{player}>'s Choice: `None`"
            try:
                member = interaction.guild.get_member(player)
                member.remove_roles(player_role)
            except:
                pass
        embed = nextcord.Embed(title="One of a Kind Results", description=descp)
        player_mentions.append(interaction.user.mention)
        await msg.channel.send(content=f"{' '.join(player_mentions)}", embed=embed)
        collection.delete_one({"_id": interaction.channel.id})
        
        
            
def setup(bot):
    bot.add_cog(OneOfAKind(bot))
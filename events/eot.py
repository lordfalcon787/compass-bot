import nextcord
import random
import asyncio
from nextcord.ext import commands, application_checks
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["EOT"]
DESCP = f"Welcome to The Evolution of Trust. \n\n Each round you select if you want to contribute a coin or not. Both players start with 5 coins. If you contribute a coin, the other person receives 4 coins (and you lose your one coin). The other person has the same option. However, if you refuse to contribute a coin for two or more rounds in a row, the bot will roll [the number rounds you have went without giving] to determine your penalty to subtract from your coin count. \n\n First to 15 wins or if the other person reaches negatives."

class JoinView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Join", style=nextcord.ButtonStyle.green, custom_id="eot_join")
        button.callback = self.join_callback
        self.add_item(button)

    async def join_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if doc is None:
            await interaction.send("This game has already ended or does not exist.", ephemeral=True)
            return
        players = doc["players"]
        if interaction.user.id in players:
            await interaction.send("You have already joined the game.", ephemeral=True)
            return
        players.append(interaction.user.id)
        collection.update_one({"_id": interaction.channel.id}, {"$set": {"players": players}})
        embed = nextcord.Embed(title="Join Success", description="You have joined the game successfully.", color=nextcord.Color.green())
        await interaction.send(embed=embed, ephemeral=True)

class GameView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Contribute", style=nextcord.ButtonStyle.green, custom_id="eot_contribute")
        button.callback = self.contribute_callback
        self.add_item(button)

    async def contribute_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if doc is None:
            await interaction.send("This game has already ended or does not exist.", ephemeral=True)
            return
        winners = doc.get("winners", [])
        if interaction.user.id not in winners:
            await interaction.send("You are not a part of this game.", ephemeral=True)
            return
        collection.update_one({"_id": interaction.channel.id}, {"$set": {f"{interaction.user.id}": True, f"{interaction.user.id}_rounds": 0}})
        await interaction.send("You have contributed.", ephemeral=True)

class Override(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Override", style=nextcord.ButtonStyle.red, custom_id="eot_override")
        button.callback = self.override_callback
        self.add_item(button)

    async def override_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        doc = collection.find_one({"_id": interaction.channel.id})
        if doc is None:
            await interaction.send("This game has already ended or does not exist.", ephemeral=True)
            return
        host = doc["host"]
        if interaction.user.id != host:
            await interaction.send("You are not the host of this game.", ephemeral=True)
            return
        collection.delete_one({"_id": interaction.channel.id})
        await interaction.send("Game overridden successfully.", ephemeral=True)

class EOT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("EOT cog loaded")
        self.bot.add_view(JoinView())
        self.bot.add_view(GameView())
        self.bot.add_view(Override())

    @nextcord.slash_command(name="eot", description="Run an Evolution of Trust game.")
    @application_checks.guild_only()
    async def eot(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=False)
        descp = DESCP
        check = collection.find_one({"_id": interaction.channel.id})
        if check is not None:
            embed = nextcord.Embed(title="Error Detected", description="A game has already started in this channel. Would you like to override the game?", color=nextcord.Color.red())
            await interaction.send(embed=embed, view=Override(), ephemeral=False)
            return
        embed = nextcord.Embed(title="Evolution of Trust", description=descp, color=nextcord.Color.green())
        embed.set_footer(text="You have 75 seconds to join the game.", icon_url=interaction.guild.icon.url)
        view = JoinView()
        msg = await interaction.send(embed=embed, view=view, ephemeral=False)
        collection.insert_one({"_id": msg.channel.id, "players": [], "winners": [], "host": interaction.user.id})
        await asyncio.sleep(75)
        doc = collection.find_one({"_id": msg.channel.id})
        if len(doc["players"]) < 2:
            await msg.reply("There were not enough players to start the game.", mention_author=False)
            collection.delete_one({"_id": msg.channel.id})
            await msg.edit(view=None)
            return
        players = doc["players"]
        winners = random.sample(players, 2)
        collection.update_one({"_id": msg.channel.id}, {"$set": {"winners": winners, f"{winners[0]}": False, f"{winners[1]}": False, f"{winners[0]}_coins": 5, f"{winners[1]}_coins": 5, f"{winners[0]}_rounds": 0, f"{winners[1]}_rounds": 0, "round": 1}})
        await msg.reply(f"<@{winners[0]}>, <@{winners[1]}>")
        descp = f"> <@{winners[0]}> Coins: `5` \n> <@{winners[1]}> Coins: `5`\n\n{descp}"
        embed.description = descp
        embed.set_footer(text="Round 1 - You have 15 seconds to choose.")
        view = GameView()
        await msg.edit(content=f"<@{winners[0]}> <@{winners[1]}>", embed=embed, view=view)
        await asyncio.sleep(15)
        await self.eot_game(msg)

    async def eot_game(self, msg):
        await msg.edit(view=None)
        channel = self.bot.get_channel(msg.channel.id)
        doc = collection.find_one({"_id": msg.channel.id})
        descp = DESCP
        embed = nextcord.Embed(title="Evolution of Trust", description=descp, color=nextcord.Color.green())
        winners = doc["winners"]
        winner_1_choice = doc[f"{winners[0]}"]
        winner_2_choice = doc[f"{winners[1]}"]
        winner_1_coins = doc[f"{winners[0]}_coins"]
        winner_2_coins = doc[f"{winners[1]}_coins"]
        winner_1_rounds = doc[f"{winners[0]}_rounds"]
        winner_2_rounds = doc[f"{winners[1]}_rounds"]

        if winner_1_choice is True:
            winner_2_coins += 4
            winner_1_coins -= 1
        else:
            winner_1_rounds += 1

        if winner_2_choice is True:
            winner_1_coins += 4
            winner_2_coins -= 1
        else:
            winner_2_rounds += 1

        random_num = 2
        if winner_1_rounds >= random_num:
            deduction = random.randint(1, winner_1_rounds)
            winner_1_coins -= deduction
            embed_deduct = nextcord.Embed(title="Random Event", description=f"<@{winners[0]}> lost `{deduction}` coins due to not contributing!", color=nextcord.Color.red())
            await channel.send(embed=embed_deduct)
            await asyncio.sleep(1)

        if winner_2_rounds >= random_num:
            deduction = random.randint(1, winner_2_rounds)
            winner_2_coins -= deduction
            embed_deduct = nextcord.Embed(title="Random Event", description=f"<@{winners[1]}> lost `{deduction}` coins due to not contributing!", color=nextcord.Color.red())
            await channel.send(embed=embed_deduct)
            await asyncio.sleep(1)
            
        if winner_1_coins >= 15 and winner_2_coins >= 15:
            if winner_1_coins > winner_2_coins:
                descp = f"<@{winners[0]}> wins with `{winner_1_coins}` coins!"
            elif winner_2_coins > winner_1_coins:
                descp = f"<@{winners[1]}> wins with `{winner_2_coins}` coins!"
            else:
                descp = f"It's a tie! Both players have `{winner_1_coins}` coins!"
            embed.description = descp
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return
        elif winner_1_coins >= 15:
            descp = f"<@{winners[0]}> wins with `{winner_1_coins}` coins!"
            embed.description = descp
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return
        elif winner_2_coins >= 15:
            descp = f"<@{winners[1]}> wins with `{winner_2_coins}` coins!"
            embed.description = descp 
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return
        elif winner_1_coins < 0 and winner_2_coins < 0:
            if winner_1_coins > winner_2_coins:
                descp = f"<@{winners[0]}> wins with `{winner_1_coins}` coins because they lost less!"
            elif winner_2_coins > winner_1_coins:
                descp = f"<@{winners[1]}> wins with `{winner_2_coins}` coins because they lost less!"
            else:
                descp = f"Both players went bankrupt with `{winner_1_coins}` coins!"
            embed.description = descp
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return
        elif winner_1_coins < 0:
            descp = f"<@{winners[1]}> wins because <@{winners[0]}> went bankrupt!"
            embed.description = descp
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return
        elif winner_2_coins < 0:
            descp = f"<@{winners[0]}> wins because <@{winners[1]}> went bankrupt!"
            embed.description = descp
            embed.set_footer(text="Game Over!")
            await channel.send(content=f"<@{winners[0]}> <@{winners[1]}> <@{doc['host']}>", embed=embed)
            await msg.delete()
            collection.delete_one({"_id": msg.channel.id})
            return

        round = doc["round"] + 1
        collection.update_one({"_id": msg.channel.id}, {"$set": {f"{winners[0]}": False, f"{winners[1]}": False, f"{winners[0]}_coins": winner_1_coins, f"{winners[1]}_coins": winner_2_coins, f"{winners[0]}_rounds": winner_1_rounds, f"{winners[1]}_rounds": winner_2_rounds, "round": round}})

        descp = f"> <@{winners[0]}> Coins: `{winner_1_coins}` \n> <@{winners[1]}> Coins: `{winner_2_coins}`\n\n{descp}"
        if winner_1_choice is True and winner_2_choice is True:
            descp = f"Both players decided to contribute! \n\n{descp}"
        elif winner_1_choice is True:
            descp = f"<@{winners[0]}> decided to contribute! \n\n{descp}"
        elif winner_2_choice is True:
            descp = f"<@{winners[1]}> decided to contribute! \n\n{descp}"
        else:
            descp = f"Both players decided not to contribute! \n\n{descp}"
        embed.description = descp
        embed.set_footer(text=f"Round {round} - You have 15 seconds to choose.")
        old_msg = msg
        msg = await channel.send(content=f"<@{winners[0]}> <@{winners[1]}>", embed=embed, view=GameView())
        await old_msg.delete()
        await asyncio.sleep(15)
        asyncio.create_task(self.eot_game(msg))
        return
    
def setup(bot):
    bot.add_cog(EOT(bot))
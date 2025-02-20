import nextcord
from nextcord.ext import commands, application_checks
import asyncio
from nextcord import SlashOption
from utils.mongo_connection import MongoConnection
import random

RC_ID = 1205270486230110330

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Rollkill"]
configuration = db["Configuration"]

class RollkillView(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Join", style=nextcord.ButtonStyle.primary, custom_id="join_rollkill")
        button.callback = self.button_callback
        self.add_item(button)

    async def button_callback(self, interaction: nextcord.Interaction):
        if interaction.user.id not in collection.find_one({"_id": interaction.channel.id})["players"]:
            collection.update_one({"_id": interaction.channel.id}, {"$push": {"players": interaction.user.id}})
            await interaction.response.send_message("You have joined the game.", ephemeral=True)
        else:
            await interaction.response.send_message("You are already in the game.", ephemeral=True)

class Rollkill(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.rollkill_lock = asyncio.Lock()

    @commands.Cog.listener()
    async def on_ready(self):
        print("Rollkill cog loaded.")

    @commands.command(name="rollkill")
    async def rollkill_command(self, ctx):
        async with self.rollkill_lock:
            doc = collection.find_one({"_id": ctx.channel.id})
            if not doc:
                await ctx.reply("No game is currently running in this channel.", mention_author=False)
                return
            elif len(ctx.message.content.split(" ")) > 1:
                await self.host_end(ctx)
                return
            elif ctx.author.id not in doc["winners"]:
                await ctx.reply("You are not in the game.", mention_author=False)
                return
            elif doc["dead_time"] is True:
                await ctx.reply("Dead time was activated, you have been eliminated from the game.", mention_author=False)
                member = ctx.guild.get_member(ctx.author.id)
                collection.update_one({"_id": ctx.channel.id}, {"$pull": {"winners": ctx.author.id}})
                doc2 = configuration.find_one({"_id": "config"})["player_role"]
                try:
                    if str(ctx.guild.id) in doc2:
                        await member.remove_roles(nextcord.utils.get(ctx.guild.roles, id=doc2[str(ctx.guild.id)]))
                except:
                    pass
                winners = collection.find_one({"_id": ctx.channel.id})["winners"]
                if len(winners) < 2:
                    await ctx.send(content=f"Only one person is left in the game, they win by default. The winner is <@{winners[0]}>.")
                    member = ctx.guild.get_member(winners[0])
                    doc2 = configuration.find_one({"_id": "config"})["player_role"]
                    try:
                        if str(ctx.guild.id) in doc2:
                            await member.remove_roles(nextcord.utils.get(ctx.guild.roles, id=doc2[str(ctx.guild.id)]))
                    except:
                        pass
                    collection.delete_one({"_id": ctx.channel.id})
                    return
                else:
                    return
            elif len(doc["winners"]) < 2:
                await self.end_game(ctx)
                return
            rand = random.randint(1, 100)
            if rand <= 10:
                asyncio.create_task(self.dead_time(ctx))
                return
            number = doc["start"]
            new_number = random.randint(1, number)
            if new_number == 1:
                await self.end_game(ctx)
                return
            collection.update_one({"_id": ctx.channel.id}, {"$set": {"start": new_number}})
            embed = nextcord.Embed(title=f"{ctx.author.name} rolls {new_number} (1-{number})")
            embed.set_footer(text="First to roll 0 wins the game.")
            await ctx.send(embed=embed, mention_author=False)

    async def host_end(self, ctx):
        split = ctx.message.content.split(" ")
        if split[1].lower() != "end":
            return
        doc = collection.find_one({"_id": ctx.channel.id})
        if doc["host"] != ctx.author.id and not ctx.author.guild_permissions.administrator:
            await ctx.reply("You are not the host of this game.", mention_author=False)
            return
        collection.delete_one({"_id": ctx.channel.id})
        await ctx.reply("Game ended successfully.", mention_author=False)
        await ctx.message.add_reaction("✅")

    async def dead_time(self, ctx):
        collection.update_one({"_id": ctx.channel.id}, {"$set": {"dead_time": True}})
        try:
            await ctx.reply(f"# Dead time has been activated for 5 seconds. \n No message will appear when it's over, roll at your own risk.", mention_author=False)
            await asyncio.sleep(5)
            collection.update_one({"_id": ctx.channel.id}, {"$set": {"dead_time": False}})
        except:
            return

    async def end_game(self, ctx):
        doc = collection.find_one({"_id": ctx.channel.id})
        embed = nextcord.Embed(title=f"{ctx.author.name} rolls 1 (1-{doc['start']})")
        embed.set_footer(text="You won the game!")
        await ctx.reply(embed=embed, mention_author=False)
        winners = doc["winners"]
        doc2 = configuration.find_one({"_id": "config"})["player_role"]
        for winner in winners:
            member = ctx.guild.get_member(winner)
            try:
                if str(ctx.guild.id) in doc2:
                    await member.remove_roles(nextcord.utils.get(ctx.guild.roles, id=doc2[str(ctx.guild.id)]))
            except:
                pass
        collection.delete_one({"_id": ctx.channel.id})

    @nextcord.slash_command(description="Rollkill is a game where you roll a die and the highest roll wins.")
    @application_checks.guild_only()
    async def rollkill(self, interaction: nextcord.Interaction,
                       number: str = SlashOption(description="The number to start with."),
                       start: int = SlashOption(description="The amount of players.", choices={5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10})):
        
        num = number
        multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
        quantity = num.lower()
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
            

        try:
            collection.insert_one({"_id": interaction.channel.id, "host": interaction.user.id, "start": quantity, "players": [], "dead_time": False})
        except:
            await interaction.response.send_message("Game already exists in this channel.", ephemeral=True)
            return
        description = "You have 1 minute to join the Rollkill by clicking the button below. \n\n This is a __new game__ so please read the instructions below. \n\n __**HOW TO PLAY:**__ \n\n Five people will be selected to play. There is no order, run the cmd `-rollkill` to roll. You can spam the cmd as much as you want and the numbers will be synchronized between all users. At some points a dead time will be activated (the bot will alert you). If you roll during the dead time (which is 5 seconds) you will be eliminated from the game. **First to ONE wins the game.**"

        embed = nextcord.Embed(title="Rollkill 2.0", description=description, color=0x00ff00)
        embed.set_footer(text=f"{interaction.guild.name} - Created by _lordfalcon_ and ace_of_spadess.", icon_url=interaction.guild.icon.url)
        await interaction.response.send_message(content=f"Game started successfully.", ephemeral=True)
        view = RollkillView()
        msg = await interaction.channel.send(embed=embed, view=view)
        await asyncio.sleep(60)
        await self.start_game(msg, start)

    async def start_game(self, msg, start):
        players = collection.find_one({"_id": msg.channel.id})["players"]
        winners = []
        if len(players) <= start:
            winners = players
        else:
            try:
                winners = random.sample(players, start)
            except:
                collection.delete_one({"_id": msg.channel.id})
                await msg.channel.send("There are not enough players to start the game with provided requirements. Please try again with different settings.")
                return
        
        descp = ""
        doc2 = configuration.find_one({"_id": "config"})["player_role"]
        for winner in winners:
            descp = f"{descp} <@{winner}>"
            member = msg.guild.get_member(winner)
            try:
                if str(msg.guild.id) in doc2:
                    await member.add_roles(nextcord.utils.get(msg.guild.roles, id=doc2[str(msg.guild.id)]))
            except:
                pass
        collection.update_one({"_id": msg.channel.id}, {"$set": {"winners": winners}})
        await msg.reply(content=descp)
        await msg.edit(embed=msg.embeds[0], view=None)

    
                
def setup(bot):
    bot.add_cog(Rollkill(bot))

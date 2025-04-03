import nextcord
from nextcord.ext import commands

class Donations(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Donations cog loaded")

def setup(bot):
    bot.add_cog(Donations(bot))
import nextcord
from nextcord.ext import commands

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"CustomCommands cog loaded.")

    


def setup(bot):
    bot.add_cog(CustomCommands(bot))
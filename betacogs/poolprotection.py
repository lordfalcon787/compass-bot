import nextcord
from nextcord.ext import commands

class PoolProtection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        

    @commands.Cog.listener()
    async def on_ready(self):
        print("Pool Protection Cog is ready")

def setup(bot):
    bot.add_cog(PoolProtection(bot))
    
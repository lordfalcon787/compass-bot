import nextcord
from nextcord.ext import commands
AUTO = [1267527896218468412, 1267530934723281009]

class Donosticky(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Donosticky cog loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id not in AUTO:
            return
        elif message.author.bot:
            return
        await message.delete(delay=1800)
                    
def setup(bot):
    bot.add_cog(Donosticky(bot))
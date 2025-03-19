import nextcord
from nextcord.ext import commands

class UnoReminder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Uno Reminder is online.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != 403419413904228352:
            return
        elif not message.embeds:
            return
        elif not message.embeds[0].description:
            return
        
        descp = message.embeds[0].description

        if "It is now" not in descp and "turn!" not in descp:
            return
        
        descp_split = descp.split("\n")
        for line in descp_split:
            if "It is now" in line:
                player_name = line.split(" ")[2].strip("'s")
                break
        
        if player_name:
            member = nextcord.utils.get(message.guild.members, name=player_name)
            if member:
                await message.reply(f'{member.mention} - it is your turn!')

def setup(bot):
    bot.add_cog(UnoReminder(bot))


        
        
            
            
            
            
            

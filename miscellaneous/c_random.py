import nextcord
import nextcord.ext.commands
from nextcord.ext import commands
DANK_ID = 270904126974590976
GREEN_CHECK = "<:green_check2:1291173532432203816>"
DANK_EVENTS = ["jack o lantern giveaway!", "dice champs", "dank memer corp", "punch pepe", "iq competition", "reverse reverse", "trivia night", "dank scrambled eggs", "fish guesser", "item guesser", "boss battle", "anti-rizz"]

class random(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Random cog loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id != DANK_ID:
            return 
        if not message.embeds:
            return 
        if not message.embeds[0].title:
            return 
        if not message.reference:
            event = message.embeds[0].title.lower()
            if event in DANK_EVENTS:
                capevent = ' '.join(word.capitalize() for word in event.split())
                embed = nextcord.Embed(title = f"Random Event Detected", description = f"A random event has been detected in this channel. Join up! \n\n The event is **{capevent}**", color = 65280)
                con = "1277490909906473062"
                img = "https://dankmemer.lol/img/memer.webp"
                embed.set_thumbnail(url = img)
                embed.set_footer(text = f"{capevent}", icon_url = img)
                await message.reply(content = f"<@&{con}>", embed = embed)

def setup(bot):
    bot.add_cog(random(bot))
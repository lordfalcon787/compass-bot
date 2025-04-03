import nextcord
from nextcord.ext import commands
from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]

MAFIA_BOTS = [758999095070687284, 511786918783090688, 204255221017214977]

class Mafia(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Mafia cog loaded.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.id not in MAFIA_BOTS:
            return
        elif message.guild.id != 1205270486230110330:
            return
        elif not message.embeds:
            return
        elif not message.embeds[0].title:
            return

        if "role list" in message.embeds[0].title.lower():
            await self.mafia_rules(message)
            return
        
    async def mafia_rules(self, message):
        embed = nextcord.Embed(
            title="Robbing Central Mafia Rules",
            description="**1) DMing/Teaming Rules:**\n"
                        "- __Villager__: Do _not_ DM villager roles. Do _not_ DM anyone if you're a villager role. This includes Santa's child and mayor.\n"
                        "- __Mafia/Neutral__: If you're a mafia or neutral, you may DM other mafias or neutrals _only if_ they can win with you. Do _not_ team with anyone who you cannot win with.\n"
                        "- __Submissor and Isekai__ have their own DM rules: [View](https://discord.com/channels/1205270486230110330/1265160374534275124/1322563077547233361)\n\n"
                        "**2) General Rules:**\n"
                        "- Do not go __AFK__ during the game. Actively participate in the mafia channel to avoid confusion.\n"
                        "- __Screenshotting or Copy-Pasting__ game info is not allowed.\n"
                        "- __Dead Players__ are not allowed to share information about the game except mafias/neutrals with their teammates, or in the mafia channel with the Talking Dead anomaly.\n"
                        "- __Throwing__: Anything that intentionally harms your teammates is not allowed.\n"
                        "- __Targeting__: Setting bounties on players is not allowed. Avoid killing the same player early in multiple mafias.\n"
                        "- __Use common sense and play fair__: Some rules are too obvious to be mentioned, so you may be punished even if you don't violate any rules listed here.\n\n"
                        "**3) Punishments:** The punishments for violating mafia rules are listed [here](https://discord.com/channels/1205270486230110330/1265160374534275124/1303049015285383230). If you think you received an unfair punishment, or if you'd like to report someone else for breaking the rules, you may contact the host or open a ticket in <#1205270487085879428>.",
            color=nextcord.Color.blue()
        )
        embed.set_footer(text="Made by chocothefirst", icon_url=message.guild.icon.url)
        await message.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Mafia(bot))
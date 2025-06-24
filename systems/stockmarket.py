import nextcord
import requests
from nextcord.ext import commands

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("StockMarket cog loaded")

    @commands.command(name="stocks")
    async def stockmarket_cmd(self, ctx):
        await ctx.send("Stock market command")

def setup(bot):
    bot.add_cog(StockMarket(bot))
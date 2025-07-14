import nextcord
import finnhub
from datetime import datetime, timedelta
from nextcord.ext import commands
import json

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = "d1qksn9r01qo4qd7spq0d1qksn9r01qo4qd7spqg"
        self.finnhub_client = finnhub.Client(api_key=self.api_key)

    @commands.Cog.listener()
    async def on_ready(self):
        print("StockMarket cog loaded")

    async def get_stock_data(self, symbol):
        """Fetch current stock quote data"""
        try:
            quote = self.finnhub_client.quote(symbol)
            
            if 'c' not in quote or quote['c'] == 0:
                return [], []
            
            current_price = float(quote['c'])  
            previous_close = float(quote['pc']) 
            
            today = datetime.now().strftime("%Y-%m-%d")
            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            
            return [today, yesterday], [current_price, previous_close]
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return [], []


    @nextcord.slash_command(name="stocks", description="View the current stock market.")
    async def stocks(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
         
        indices = {
            "DIA": "SPDR Dow Jones",
            "QQQ": "NASDAQ Invesco", 
            "SPY": "SPDR S&P 500",
            "NVDA": "NVIDIA Corporation",
            "TSLA": "Tesla Inc.",
            "AAPL": "Apple Inc.",
            "MSFT": "Microsoft",
            "GOOG": "Alphabet Inc.",
            "META": "Meta Platforms",
        }
        
        data_dict = {}
        embed_data = {}
        
        for symbol, name in indices.items():
            dates, prices = await self.get_stock_data(symbol)
            data_dict[symbol] = (dates, prices)
            
            if len(prices) >= 2:
                current_price = prices[0]
                prev_price = prices[1]
                change = current_price - prev_price
                change_percent = round((change / prev_price * 100), 2) if prev_price != 0 else 0
            else:
                current_price = prices[0] if prices else 0
                prev_price = 0
                change = 0
                change_percent = 0
            
            embed_data[symbol] = {
                "name": name,
                "current": current_price,
                "previous": prev_price,
                "change": change,
                "change_percent": change_percent
            }
        
        embed = nextcord.Embed(
            title="📈 Stock Market Overview",
            description="Current prices for selected stocks.",
            color=0x00ff00 if any(data["change"] > 0 for data in embed_data.values()) else 0xff0000,
            timestamp=datetime.now()
        )
        
        for symbol, data in embed_data.items():
            emoji = "🟢" if data["change"] >= 0 else "🔴"
            sign = "+" if data["change"] >= 0 else ""
            
            embed.add_field(
                name=f"{emoji} {data['name']}",
                value=f"**Current: ${data['current']}**\n"
                      f"**Previous: ${data['previous']}**\n"
                      f"**Change: ${round(data['change'], 2)} ({sign}{data['change_percent']}%)**",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(StockMarket(bot))
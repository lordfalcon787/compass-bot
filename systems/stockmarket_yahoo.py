import nextcord
import requests
from datetime import datetime, timedelta
from nextcord.ext import commands
import json

class StockMarketYahoo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("StockMarketYahoo cog loaded")

    async def get_yahoo_stock_data(self, symbol):
        """Fetch current stock data from Yahoo Finance API"""
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            
            params = {
                "range": "2d",
                "interval": "1d"
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            if "chart" not in data or not data["chart"]["result"]:
                print(f"No data for {symbol}")
                return [], []
            
            result = data["chart"]["result"][0]
            timestamps = result["timestamp"]
            prices = result["indicators"]["quote"][0]["close"]
            
            recent_prices = []
            recent_dates = []
            
            for i in range(min(2, len(timestamps))):
                if prices[-(i+1)] is not None:
                    recent_prices.append(prices[-(i+1)])
                    date = datetime.fromtimestamp(timestamps[-(i+1)]).strftime("%Y-%m-%d")
                    recent_dates.append(date)
            
            return recent_dates, recent_prices
            
        except Exception as e:
            print(f"Error fetching Yahoo data for {symbol}: {e}")
            return [], []

    @nextcord.slash_command(name="stocks_yahoo", description="View current stock market data from Yahoo Finance.")
    async def stocks_yahoo(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        
        indices = {
            "^DJI": "Dow Jones Industrial Average",
            "^IXIC": "NASDAQ Composite", 
            "^GSPC": "S&P 500"
        }
        
        embed = nextcord.Embed(
            title="📈 Stock Market Overview (Yahoo Finance)",
            description="Current prices for major market indices",
            color=0x1f77b4,
            timestamp=datetime.now()
        )
        
        for symbol, name in indices.items():
            dates, prices = await self.get_yahoo_stock_data(symbol)
            
            if len(prices) >= 2:
                current_price = prices[0]
                prev_price = prices[1]
                change = current_price - prev_price
                change_percent = (change / prev_price * 100) if prev_price != 0 else 0
            elif len(prices) == 1:
                current_price = prices[0]
                prev_price = current_price
                change = 0
                change_percent = 0
            else:
                current_price = 0
                prev_price = 0
                change = 0
                change_percent = 0
            
            emoji = "🟢" if change >= 0 else "🔴"
            sign = "+" if change >= 0 else ""
            
            embed.add_field(
                name=f"{emoji} {name}",
                value=f"**Current: ${current_price}**\n"
                      f"**Previous: ${prev_price}**\n"
                      f"{sign}${change} ({sign}{change_percent}%)",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(StockMarketYahoo(bot)) 
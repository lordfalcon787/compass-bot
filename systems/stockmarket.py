import nextcord
import requests
from datetime import datetime, timedelta
from nextcord.ext import commands
import json

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = "1KC86XG04LX81C91"

    @commands.Cog.listener()
    async def on_ready(self):
        print("StockMarket cog loaded")

    async def get_stock_data(self, symbol):
        """Fetch stock data for the last 2 days"""
        try:
            url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}'
            
            response = requests.get(url)
            data = response.json()
            
            print(f"API response for {symbol}: {data}")
            
            if "Time Series (Daily)" not in data:
                print(f"No time series data for {symbol}. Response: {data}")
                return [], []
            
            time_series = data["Time Series (Daily)"]
            dates = sorted(time_series.keys(), reverse=True)
            
            recent_dates = dates[:2]
            recent_prices = []
            
            for date in recent_dates:
                recent_prices.append(float(time_series[date]["4. close"]))
            
            return recent_dates, recent_prices
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return [], []


    @nextcord.slash_command(name="stocks", description="View the current stock market.")
    async def stocks(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        
        indices = {
            "DJI": "Dow Jones Industrial Average",
            "IXIC": "NASDAQ Composite", 
            "SPX": "S&P 500"
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
                change_percent = (change / prev_price * 100) if prev_price != 0 else 0
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
            description="Current prices for major market indices",
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
                      f"{sign}${data['change']} ({sign}{data['change_percent']}%)",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(StockMarket(bot))
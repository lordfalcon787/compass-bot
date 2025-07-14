import nextcord
import requests
from datetime import datetime, timedelta
from nextcord.ext import commands
import json

class StockMarket(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_key = "1KC86XG04LX81C91"
        self.base_url = "https://www.alphavantage.co/query"

    @commands.Cog.listener()
    async def on_ready(self):
        print("StockMarket cog loaded")

    async def get_stock_data(self, symbol):
        """Fetch stock data for the last 7 days"""
        try:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.api_key,
                "outputsize": "compact"
            }
            
            response = requests.get(self.base_url, params=params)
            data = response.json()
            
            if "Time Series (Daily)" not in data:
                return self.get_demo_data(symbol)
            
            time_series = data["Time Series (Daily)"]
            dates = []
            prices = []
            
            for i in range(7):
                date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
                if date in time_series:
                    dates.append(date)
                    prices.append(float(time_series[date]["4. close"]))
            
            return list(reversed(dates)), list(reversed(prices))
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return self.get_demo_data(symbol)

    def get_demo_data(self, symbol):
        """Generate demo data for testing purposes"""
        dates = []
        prices = []
        base_prices = {
            "DJI": 35000,
            "IXIC": 14000,
            "GSPC": 4500
        }
        
        base_price = base_prices.get(symbol, 100)
        
        for i in range(7):
            date = (datetime.now() - timedelta(days=6-i)).strftime("%Y-%m-%d")
            dates.append(date)
            variation = (i - 3) * 0.02
            prices.append(base_price * (1 + variation))
        
        return dates, prices



    @nextcord.slash_command(name="stocks", description="View the current stock market.")
    async def stocks(self, interaction: nextcord.Interaction):
        await interaction.response.defer()
        
        indices = {
            "DJI": "Dow Jones Industrial Average",
            "IXIC": "NASDAQ Composite",
            "GSPC": "S&P 500"
        }
        
        data_dict = {}
        embed_data = {}
        
        for symbol, name in indices.items():
            dates, prices = await self.get_stock_data(symbol)
            data_dict[symbol] = (dates, prices)
            
            current_price = prices[-1] if prices else 0
            prev_price = prices[-2] if len(prices) > 1 else current_price
            change = current_price - prev_price
            change_percent = (change / prev_price * 100) if prev_price != 0 else 0
            
            embed_data[symbol] = {
                "name": name,
                "current": current_price,
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
            
            # Get the last two days of prices
            dates, prices = data_dict[symbol]
            current_price = prices[-1] if prices else 0
            prev_price = prices[-2] if len(prices) > 1 else current_price
            
            embed.add_field(
                name=f"{emoji} {data['name']}",
                value=f"**Current: ${current_price}**\n"
                      f"**Previous: ${prev_price}**\n"
                      f"{sign}${data['change']} ({sign}{data['change_percent']}%)",
                inline=True
            )
        
        await interaction.followup.send(embed=embed)

def setup(bot):
    bot.add_cog(StockMarket(bot))
import nextcord
from nextcord.ext import commands
from openai import OpenAI
import json
import time

_last_summarize_time = 0

with open("config.json", "r") as file:
    config = json.load(file)

loading_emoji = "<a:loading_animation:1218134049780928584>"
GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

class Summarize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(Summarize, '_client'):
            Summarize._client = OpenAI(
                api_key=config["api_key"],
                base_url="https://openrouter.ai/api/v1"
            )
        self.client = Summarize._client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Summarize cog loaded.")

    @commands.command(name="summarize")
    async def summarize(self, ctx):
        global _last_summarize_time
        now = time.time()
        if now - _last_summarize_time < 60:
            await ctx.reply("This command can only be used once per minute. Please wait a bit before trying again.", mention_author=False)
            return
        _last_summarize_time = now

        if not ctx.message.reference:
            await ctx.reply("Please reply to a message to summarize it.", mention_author=False)
            return
        await ctx.message.add_reaction(loading_emoji)
        message = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        
        try:
            response = self.client.chat.completions.create(
                model="nousresearch/deephermes-3-llama-3-8b-preview:free",
                messages=[
                    {
                        "role": "user", 
                        "content": f"Summarize the following text in 2 sentences or less: {message.content}"
                    }
                ]
            )
            response = response.choices[0].message.content
            embed = nextcord.Embed(
                title="Message Summary",
                description=response,
                color=nextcord.Color.blurple()
            )
            embed.set_footer(text=f"Requested by {ctx.author}")
            await ctx.message.clear_reactions()
            await ctx.message.add_reaction(GREEN_CHECK)
            await ctx.message.reference.resolved.reply(embed=embed, mention_author=False)
            
        except Exception as e:
            await ctx.message.clear_reactions()
            print(e)
            await ctx.reply("Sorry, there was an error summarizing that message.", mention_author=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        elif message.channel.id == 1265160374534275124:
            return
        words = message.content.split()
        if len(words) > 100:
            try:
                response = self.client.chat.completions.create(
                    model="nousresearch/hermes-3-llama-3.1-405b:free",
                    messages=[
                        {
                            "role": "user",
                            "content": f"Summarize the following text in 2 sentences or less: {message.content}"
                        }
                    ]
                )
                response = response.choices[0].message.content
                embed = nextcord.Embed(
                    title="Message Summary", 
                    description=response,
                    color=nextcord.Color.blurple()
                )
                embed.set_footer(text=f"Requested fullfilled automatically by bot.")
                
                await message.reply(embed=embed, mention_author=False)
                
            except:
                pass

    def cog_unload(self):
        if hasattr(Summarize, '_client'):
            delattr(Summarize, '_client')

def setup(bot):
    bot.add_cog(Summarize(bot))
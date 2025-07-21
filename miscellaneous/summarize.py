import nextcord
from nextcord.ext import commands
from openai import OpenAI

api_key = "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"

class Summarize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(Summarize, '_client'):
            Summarize._client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        self.client = Summarize._client
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Summarize cog loaded.")

    @commands.command(name="summarize")
    async def summarize(self, ctx):
        if not ctx.message.reference:
            await ctx.reply("Please reply to a message to summarize it.", mention_author=False)
            return
            
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
            
            await ctx.message.add_reaction("✅")
            await ctx.message.reference.resolved.reply(embed=embed, mention_author=False)
            
        except Exception as e:
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
import nextcord
from nextcord.ext import commands
from nextcord import SlashOption
from datetime import datetime, timedelta
from typing import Optional
from .transcript import TranscriptGenerator, create_channel_transcript

class TranscriptCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.generator = TranscriptGenerator()
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("Transcript cog loaded.")
    
    @nextcord.slash_command(name="transcript", description="Generate a transcript for a channel")
    async def transcript_slash(self, 
                               interaction: nextcord.Interaction,
                               channel: Optional[nextcord.TextChannel] = SlashOption(
                                   description="The channel to create a transcript for (defaults to current channel)",
                                   required=False
                               ),
                               messages: int = SlashOption(
                                   description="Number of messages to include (default: 100, max: 1000)",
                                   required=False,
                                   default=100,
                                   min_value=1,
                                   max_value=1000
                               ),
                               days_back: Optional[int] = SlashOption(
                                   description="Only include messages from the last X days",
                                   required=False,
                                   min_value=1,
                                   max_value=30
                               )):
        await interaction.response.defer(ephemeral=True)
        
        if channel is None:
            channel = interaction.channel
        
        if not channel.permissions_for(interaction.user).read_message_history:
            await interaction.followup.send(
                "You don't have permission to read message history in that channel.",
                ephemeral=True
            )
            return
        
        try:
            after = None
            if days_back:
                after = datetime.now() - timedelta(days=days_back)
            
            transcript_file = await self.generator.generate_transcript_file(
                channel=channel,
                limit=messages,
                after=after
            )
            
            embed = nextcord.Embed(
                title="📄 Channel Transcript Generated",
                description=f"Generated transcript for {channel.mention}",
                color=nextcord.Color.green()
            )
            embed.add_field(name="Messages", value=f"{messages} messages", inline=True)
            if days_back:
                embed.add_field(name="Time Range", value=f"Last {days_back} days", inline=True)
            embed.set_footer(text=f"Requested by {interaction.user}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(
                embed=embed,
                file=transcript_file,
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while generating the transcript: {str(e)}",
                ephemeral=True
            )
    
    @commands.command(name="transcript")
    @commands.has_permissions(read_message_history=True)
    async def transcript_command(self, 
                                 ctx: commands.Context, 
                                 channel: Optional[nextcord.TextChannel] = None,
                                 messages: int = 100):
        if channel is None:
            channel = ctx.channel
        
        if not channel.permissions_for(ctx.author).read_message_history:
            await ctx.send("You don't have permission to read message history in that channel.")
            return
        
        messages = min(max(1, messages), 1000)
        
        status_msg = await ctx.send(f"Generating transcript for {channel.mention}... 📝")
        
        try:
            transcript_file = await self.generator.generate_transcript_file(
                channel=channel,
                limit=messages
            )
            
            await status_msg.delete()
            
            embed = nextcord.Embed(
                title="📄 Channel Transcript Generated",
                description=f"Generated transcript for {channel.mention}",
                color=nextcord.Color.green()
            )
            embed.add_field(name="Messages", value=f"{messages} messages", inline=True)
            embed.add_field(name="Channel", value=channel.mention, inline=True)
            embed.set_footer(text=f"Requested by {ctx.author}")
            embed.timestamp = datetime.now()
            
            await ctx.send(embed=embed, file=transcript_file)
            
        except Exception as e:
            await status_msg.edit(content=f"An error occurred: {str(e)}")
    
    @nextcord.slash_command(name="quicktranscript", description="Generate a quick transcript of the last 50 messages")
    async def quick_transcript(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        
        try:
            transcript_file = await create_channel_transcript(
                channel=interaction.channel,
                limit=50
            )
            
            await interaction.followup.send(
                content="Here's a quick transcript of the last 50 messages:",
                file=transcript_file,
                ephemeral=True
            )
            
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred: {str(e)}",
                ephemeral=True
            )
    
    @commands.command(name="exportchat")
    @commands.has_permissions(administrator=True)
    async def export_chat(self, ctx: commands.Context, days: int = 7):
        days = min(max(1, days), 30)
        
        status_msg = await ctx.send(f"Exporting chat history from the last {days} days... 📊")
        
        try:
            after = datetime.now() - timedelta(days=days)
            
            transcript_file = await self.generator.generate_transcript_file(
                channel=ctx.channel,
                after=after
            )
            
            await status_msg.delete()
            
            embed = nextcord.Embed(
                title="📊 Chat History Export",
                description=f"Exported chat history from {ctx.channel.mention}",
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Time Range", value=f"Last {days} days", inline=True)
            embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
            embed.set_footer(text=f"Exported by {ctx.author}")
            embed.timestamp = datetime.now()
            
            await ctx.send(embed=embed, file=transcript_file)
            
        except Exception as e:
            await status_msg.edit(content=f"An error occurred: {str(e)}")


def setup(bot):
    bot.add_cog(TranscriptCog(bot))
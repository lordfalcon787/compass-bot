"""
Example usage of the TranscriptGenerator class.

This file demonstrates how to use the transcript functionality
in various scenarios.
"""

import asyncio
import nextcord
from datetime import datetime, timedelta
from transcript import TranscriptGenerator, create_channel_transcript


async def example_basic_transcript(channel: nextcord.TextChannel):
    """
    Example 1: Generate a basic transcript with default settings.
    """
    generator = TranscriptGenerator()
    
    # Generate transcript for last 100 messages
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        limit=100
    )
    
    print(f"Generated transcript: {transcript_file.filename}")
    return transcript_file


async def example_time_range_transcript(channel: nextcord.TextChannel):
    """
    Example 2: Generate a transcript for messages from the last 7 days.
    """
    generator = TranscriptGenerator()
    
    # Calculate 7 days ago
    seven_days_ago = datetime.now() - timedelta(days=7)
    
    # Generate transcript
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        after=seven_days_ago
    )
    
    print(f"Generated transcript for last 7 days: {transcript_file.filename}")
    return transcript_file


async def example_date_range_transcript(channel: nextcord.TextChannel):
    """
    Example 3: Generate a transcript for a specific date range.
    """
    generator = TranscriptGenerator()
    
    # Define date range
    start_date = datetime(2024, 1, 1)  # January 1, 2024
    end_date = datetime(2024, 1, 31)   # January 31, 2024
    
    # Generate transcript
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        after=start_date,
        before=end_date
    )
    
    print(f"Generated transcript for January 2024: {transcript_file.filename}")
    return transcript_file


async def example_html_string_transcript(channel: nextcord.TextChannel):
    """
    Example 4: Generate HTML string instead of file.
    """
    generator = TranscriptGenerator()
    
    # Generate HTML string
    html_content = await generator.generate_transcript(
        channel=channel,
        limit=50
    )
    
    # You can now use this HTML string however you want
    # For example, save it to a database, send it via email, etc.
    print(f"Generated HTML transcript with {len(html_content)} characters")
    
    # Save to file manually if needed
    with open("custom_transcript.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    return html_content


async def example_quick_transcript(channel: nextcord.TextChannel):
    """
    Example 5: Use the convenience function for quick transcript generation.
    """
    # This is the simplest way to generate a transcript
    transcript_file = await create_channel_transcript(
        channel=channel,
        limit=200
    )
    
    print(f"Quick transcript generated: {transcript_file.filename}")
    return transcript_file


async def example_filtered_transcript(channel: nextcord.TextChannel, user_id: int):
    """
    Example 6: Generate a transcript and filter messages programmatically.
    
    Note: This example shows how you might extend the functionality
    to filter messages by user (not built into the base class).
    """
    generator = TranscriptGenerator()
    
    # Fetch messages
    messages = []
    async for message in channel.history(limit=500):
        if message.author.id == user_id:
            messages.append(message)
    
    # For this example, we'd need to extend the TranscriptGenerator
    # to accept a list of messages directly
    print(f"Found {len(messages)} messages from user {user_id}")
    
    # You could modify the TranscriptGenerator class to accept
    # a list of messages instead of fetching them from the channel


class CustomTranscriptGenerator(TranscriptGenerator):
    """
    Example 7: Extend the TranscriptGenerator for custom functionality.
    """
    
    def _parse_discord_markdown(self, text: str) -> str:
        """Override to add custom markdown parsing."""
        # Call parent method first
        text = super()._parse_discord_markdown(text)
        
        # Add custom parsing (e.g., custom emojis)
        text = text.replace(":custom_emoji:", "🎉")
        
        return text
    
    def _generate_message_html(self, message: nextcord.Message) -> str:
        """Override to add custom message formatting."""
        # You could add special handling for bot messages, 
        # system messages, or messages with specific content
        
        if message.author.bot:
            # Add a special class for bot messages
            html = super()._generate_message_html(message)
            html = html.replace('class="message"', 'class="message bot-message"')
            return html
        
        return super()._generate_message_html(message)


# Example of using the transcript in a bot command
async def transcript_command_example(ctx, channel: nextcord.TextChannel = None):
    """
    Example of how you might use this in a bot command.
    """
    if channel is None:
        channel = ctx.channel
    
    # Check permissions
    if not channel.permissions_for(ctx.author).read_message_history:
        await ctx.send("You don't have permission to read that channel!")
        return
    
    # Generate transcript
    try:
        async with ctx.typing():
            transcript_file = await create_channel_transcript(
                channel=channel,
                limit=100
            )
        
        # Send the file
        await ctx.send(
            f"Here's the transcript for {channel.mention}:",
            file=transcript_file
        )
    
    except Exception as e:
        await ctx.send(f"Error generating transcript: {e}")


if __name__ == "__main__":
    # This won't run directly as it needs a Discord bot context
    # These are just examples of how to use the transcript functionality
    print("See the examples above for how to use the TranscriptGenerator!") 
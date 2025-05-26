import asyncio
import nextcord
from datetime import datetime, timedelta
from transcript import TranscriptGenerator, create_channel_transcript


async def example_basic_transcript(channel: nextcord.TextChannel):
    generator = TranscriptGenerator()
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        limit=100
    )
    print(f"Generated transcript: {transcript_file.filename}")
    return transcript_file


async def example_time_range_transcript(channel: nextcord.TextChannel):
    generator = TranscriptGenerator()
    seven_days_ago = datetime.now() - timedelta(days=7)
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        after=seven_days_ago
    )
    print(f"Generated transcript for last 7 days: {transcript_file.filename}")
    return transcript_file


async def example_date_range_transcript(channel: nextcord.TextChannel):
    generator = TranscriptGenerator()
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    transcript_file = await generator.generate_transcript_file(
        channel=channel,
        after=start_date,
        before=end_date
    )
    print(f"Generated transcript for January 2024: {transcript_file.filename}")
    return transcript_file


async def example_html_string_transcript(channel: nextcord.TextChannel):
    generator = TranscriptGenerator()
    html_content = await generator.generate_transcript(
        channel=channel,
        limit=50
    )
    print(f"Generated HTML transcript with {len(html_content)} characters")
    with open("custom_transcript.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    return html_content


async def example_quick_transcript(channel: nextcord.TextChannel):
    transcript_file = await create_channel_transcript(
        channel=channel,
        limit=200
    )
    print(f"Quick transcript generated: {transcript_file.filename}")
    return transcript_file


async def example_filtered_transcript(channel: nextcord.TextChannel, user_id: int):
    generator = TranscriptGenerator()
    messages = []
    async for message in channel.history(limit=500):
        if message.author.id == user_id:
            messages.append(message)
    print(f"Found {len(messages)} messages from user {user_id}")


class CustomTranscriptGenerator(TranscriptGenerator):
    def _parse_discord_markdown(self, text: str) -> str:
        text = super()._parse_discord_markdown(text)
        text = text.replace(":custom_emoji:", "🎉")
        return text
    
    def _generate_message_html(self, message: nextcord.Message) -> str:
        if message.author.bot:
            html = super()._generate_message_html(message)
            html = html.replace('class="message"', 'class="message bot-message"')
            return html
        return super()._generate_message_html(message)


async def transcript_command_example(ctx, channel: nextcord.TextChannel = None):
    if channel is None:
        channel = ctx.channel
    if not channel.permissions_for(ctx.author).read_message_history:
        await ctx.send("You don't have permission to read that channel!")
        return
    try:
        async with ctx.typing():
            transcript_file = await create_channel_transcript(
                channel=channel,
                limit=100
            )
        await ctx.send(
            f"Here's the transcript for {channel.mention}:",
            file=transcript_file
        )
    except Exception as e:
        await ctx.send(f"Error generating transcript: {e}")


if __name__ == "__main__":
    print("See the examples above for how to use the TranscriptGenerator!")
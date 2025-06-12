import nextcord
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import html
import re
import base64
from io import BytesIO

class TranscriptGenerator:
    def __init__(self):
        self.css_styles = """
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: Whitney, "Helvetica Neue", Helvetica, Arial, sans-serif;
                background-color: #36393f;
                color: #dcddde;
                padding: 20px;
                line-height: 1.5;
            }
            
            .transcript-container {
                max-width: 980px;
                margin: 0 auto;
                background-color: #36393f;
                border-radius: 8px;
                overflow: hidden;
            }
            
            .header {
                background-color: #2f3136;
                padding: 16px 20px;
                border-bottom: 1px solid #202225;
                display: flex;
                align-items: center;
                gap: 12px;
            }
            
            .header-icon {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                background-color: #5865f2;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 20px;
                font-weight: bold;
            }
            
            .header-info h1 {
                font-size: 20px;
                font-weight: 600;
                margin-bottom: 4px;
            }
            
            .header-info p {
                font-size: 14px;
                color: #b9bbbe;
            }
            
            .messages-container {
                padding: 20px;
            }
            
            .message {
                display: flex;
                padding: 4px 0;
                margin: 8px 0;
                position: relative;
            }
            
            .message:hover {
                background-color: #32353b;
                border-radius: 4px;
            }
            
            .message-avatar {
                width: 40px;
                height: 40px;
                border-radius: 50%;
                margin-right: 16px;
                flex-shrink: 0;
                background-color: #5865f2;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                color: white;
            }
            
            .message-avatar img {
                width: 100%;
                height: 100%;
                border-radius: 50%;
                object-fit: cover;
            }
            
            .message-content {
                flex: 1;
                min-width: 0;
            }
            
            .message-header {
                display: flex;
                align-items: baseline;
                gap: 8px;
                margin-bottom: 4px;
            }
            
            .message-author {
                font-weight: 600;
                font-size: 16px;
                color: #ffffff;
            }
            
            .message-timestamp {
                font-size: 12px;
                color: #72767d;
            }
            
            .message-text {
                color: #dcddde;
                font-size: 16px;
                line-height: 1.375;
                word-wrap: break-word;
            }
            
            .message-text a {
                color: #00b0f4;
                text-decoration: none;
            }
            
            .message-text a:hover {
                text-decoration: underline;
            }
            
            .message-attachments {
                margin-top: 8px;
            }
            
            .attachment {
                display: inline-block;
                margin: 4px 0;
            }
            
            .attachment img {
                max-width: 400px;
                max-height: 300px;
                border-radius: 8px;
                cursor: pointer;
            }
            
            .attachment-file {
                background-color: #2f3136;
                border: 1px solid #202225;
                border-radius: 8px;
                padding: 10px 16px;
                display: inline-flex;
                align-items: center;
                gap: 8px;
                text-decoration: none;
                color: #00b0f4;
            }
            
            .attachment-file:hover {
                background-color: #393c43;
            }
            
            .embed {
                margin-top: 8px;
                max-width: 520px;
                border-radius: 4px;
                background-color: #2f3136;
                display: flex;
                overflow: hidden;
            }
            
            .embed-color-bar {
                width: 4px;
                flex-shrink: 0;
                background-color: #5865f2;
            }
            
            .embed-content {
                padding: 16px;
                flex: 1;
            }
            
            .embed-author {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 8px;
                font-size: 14px;
                font-weight: 600;
            }
            
            .embed-author img {
                width: 24px;
                height: 24px;
                border-radius: 50%;
            }
            
            .embed-title {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 8px;
                color: #00b0f4;
            }
            
            .embed-description {
                font-size: 14px;
                line-height: 1.5;
                margin-bottom: 12px;
                white-space: pre-wrap;
            }
            
            .embed-fields {
                display: grid;
                gap: 8px;
            }
            
            .embed-field {
                min-width: 0;
            }
            
            .embed-field-inline {
                display: inline-block;
                width: calc(33.33% - 8px);
                vertical-align: top;
            }
            
            .embed-field-name {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 2px;
                color: #ffffff;
            }
            
            .embed-field-value {
                font-size: 14px;
                line-height: 1.5;
                white-space: pre-wrap;
            }
            
            .embed-thumbnail {
                margin-left: 16px;
                flex-shrink: 0;
            }
            
            .embed-thumbnail img {
                max-width: 80px;
                max-height: 80px;
                border-radius: 4px;
            }
            
            .embed-image {
                margin-top: 12px;
            }
            
            .embed-image img {
                max-width: 100%;
                border-radius: 4px;
            }
            
            .embed-footer {
                display: flex;
                align-items: center;
                gap: 8px;
                margin-top: 12px;
                font-size: 12px;
                color: #72767d;
            }
            
            .embed-footer img {
                width: 20px;
                height: 20px;
                border-radius: 50%;
            }
            
            .reactions {
                display: flex;
                gap: 4px;
                margin-top: 8px;
                flex-wrap: wrap;
            }
            
            .reaction {
                background-color: #2f3136;
                border: 1px solid #2f3136;
                border-radius: 8px;
                padding: 4px 8px;
                display: flex;
                align-items: center;
                gap: 4px;
                font-size: 14px;
                cursor: pointer;
            }
            
            .reaction:hover {
                border-color: #4f545c;
            }
            
            .reaction-emoji {
                width: 16px;
                height: 16px;
            }
            
            .reaction-count {
                color: #b9bbbe;
                font-weight: 500;
            }
            
            .system-message {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 8px 16px;
                margin: 16px 0;
                color: #72767d;
                font-size: 14px;
            }
            
            .system-message-icon {
                width: 16px;
                height: 16px;
                flex-shrink: 0;
            }
            
            .mention {
                background-color: rgba(88, 101, 242, 0.3);
                color: #dee0fc;
                padding: 0 2px;
                border-radius: 3px;
                font-weight: 500;
            }
            
            .mention:hover {
                background-color: #5865f2;
                color: #ffffff;
            }
            
            .code-inline {
                background-color: #2f3136;
                padding: 2px 4px;
                border-radius: 3px;
                font-family: Consolas, "Andale Mono WT", "Andale Mono", "Lucida Console", monospace;
                font-size: 14px;
            }
            
            .code-block {
                background-color: #2f3136;
                border: 1px solid #202225;
                border-radius: 4px;
                padding: 12px;
                margin: 8px 0;
                font-family: Consolas, "Andale Mono WT", "Andale Mono", "Lucida Console", monospace;
                font-size: 14px;
                overflow-x: auto;
            }
            
            .spoiler {
                background-color: #202225;
                color: transparent;
                padding: 0 2px;
                border-radius: 3px;
                cursor: pointer;
                transition: all 0.1s;
            }
            
            .spoiler:hover {
                background-color: rgba(255, 255, 255, 0.1);
                color: #dcddde;
            }
            
            .divider {
                display: flex;
                align-items: center;
                margin: 20px 0;
                color: #72767d;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
            }
            
            .divider::before,
            .divider::after {
                content: "";
                flex: 1;
                height: 1px;
                background-color: #4f545c;
            }
            
            .divider-text {
                padding: 0 16px;
            }
        </style>
        """
    
    def _escape_html(self, text: str) -> str:
        return html.escape(text)
    
    def _format_timestamp(self, timestamp: datetime) -> str:
        return timestamp.strftime("%m/%d/%Y %I:%M %p")
    
    def _parse_discord_markdown(self, text: str) -> str:
        if not text:
            return ""
            
        text = self._escape_html(text)
        
        text = re.sub(r'```(.*?)```', r'<pre class="code-block">\1</pre>', text, flags=re.DOTALL)
        text = re.sub(r'`(.*?)`', r'<span class="code-inline">\1</span>', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)
        text = re.sub(r'_(.*?)_', r'<em>\1</em>', text)
        text = re.sub(r'__(.*?)__', r'<u>\1</u>', text)
        text = re.sub(r'~~(.*?)~~', r'<del>\1</del>', text)
        text = re.sub(r'\|\|(.*?)\|\|', r'<span class="spoiler">\1</span>', text)
        text = re.sub(r'(https?://[^\s]+)', r'<a href="\1" target="_blank">\1</a>', text)
        text = re.sub(r'&lt;@!?(\d+)&gt;', r'<span class="mention">@User</span>', text)
        text = re.sub(r'&lt;@&amp;(\d+)&gt;', r'<span class="mention">@Role</span>', text)
        text = re.sub(r'&lt;#(\d+)&gt;', r'<span class="mention">#channel</span>', text)
        text = text.replace('\n', '<br>')
        
        return text
    
    def _generate_embed_html(self, embed: nextcord.Embed) -> str:
        color = f"#{embed.color.value:06x}" if embed.color else "#5865f2"
        
        html_parts = [f'<div class="embed">']
        html_parts.append(f'<div class="embed-color-bar" style="background-color: {color};"></div>')
        html_parts.append('<div class="embed-content">')
        
        if embed.author.name:
            html_parts.append('<div class="embed-author">')
            if embed.author.icon_url:
                html_parts.append(f'<img src="{embed.author.icon_url}" alt="">')
            html_parts.append(f'<span>{self._escape_html(embed.author.name)}</span>')
            html_parts.append('</div>')
        
        if embed.title:
            if embed.url:
                html_parts.append(f'<div class="embed-title"><a href="{embed.url}" target="_blank">{self._escape_html(embed.title)}</a></div>')
            else:
                html_parts.append(f'<div class="embed-title">{self._escape_html(embed.title)}</div>')
        
        if embed.description:
            html_parts.append(f'<div class="embed-description">{self._parse_discord_markdown(embed.description)}</div>')
        
        if embed.fields:
            html_parts.append('<div class="embed-fields">')
            for field in embed.fields:
                inline_class = "embed-field-inline" if field.inline else ""
                html_parts.append(f'<div class="embed-field {inline_class}">')
                html_parts.append(f'<div class="embed-field-name">{self._escape_html(field.name)}</div>')
                html_parts.append(f'<div class="embed-field-value">{self._parse_discord_markdown(field.value)}</div>')
                html_parts.append('</div>')
            html_parts.append('</div>')
        
        if embed.image:
            html_parts.append('<div class="embed-image">')
            html_parts.append(f'<img src="{embed.image.url}" alt="">')
            html_parts.append('</div>')
        
        if embed.footer.text:
            html_parts.append('<div class="embed-footer">')
            if embed.footer.icon_url:
                html_parts.append(f'<img src="{embed.footer.icon_url}" alt="">')
            html_parts.append(f'<span>{self._escape_html(embed.footer.text)}</span>')
            if embed.timestamp:
                html_parts.append(f' • <span>{self._format_timestamp(embed.timestamp)}</span>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        if embed.thumbnail:
            html_parts.append('<div class="embed-thumbnail">')
            html_parts.append(f'<img src="{embed.thumbnail.url}" alt="">')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    def _generate_message_html(self, message: nextcord.Message) -> str:
        html_parts = ['<div class="message">']
        
        html_parts.append('<div class="message-avatar">')
        if message.author.avatar:
            html_parts.append(f'<img src="{message.author.avatar.url}" alt="">')
        else:
            html_parts.append(message.author.name[0].upper())
        html_parts.append('</div>')
        
        html_parts.append('<div class="message-content">')
        
        html_parts.append('<div class="message-header">')
        html_parts.append(f'<span class="message-author">{self._escape_html(message.author.display_name)}</span>')
        html_parts.append(f'<span class="message-timestamp">{self._format_timestamp(message.created_at)}</span>')
        html_parts.append('</div>')
        
        if message.content:
            html_parts.append(f'<div class="message-text">{self._parse_discord_markdown(message.content)}</div>')
        
        if message.attachments:
            html_parts.append('<div class="message-attachments">')
            for attachment in message.attachments:
                if attachment.content_type and attachment.content_type.startswith('image/'):
                    html_parts.append(f'<div class="attachment"><img src="{attachment.url}" alt="{attachment.filename}"></div>')
                else:
                    html_parts.append(f'<div class="attachment"><a href="{attachment.url}" class="attachment-file">📎 {attachment.filename}</a></div>')
            html_parts.append('</div>')
        
        for embed in message.embeds:
            html_parts.append(self._generate_embed_html(embed))
        
        if message.reactions:
            html_parts.append('<div class="reactions">')
            for reaction in message.reactions:
                html_parts.append('<div class="reaction">')
                if isinstance(reaction.emoji, str):
                    html_parts.append(f'<span class="reaction-emoji">{reaction.emoji}</span>')
                else:
                    html_parts.append(f'<span class="reaction-emoji">{reaction.emoji.name}</span>')
                html_parts.append(f'<span class="reaction-count">{reaction.count}</span>')
                html_parts.append('</div>')
            html_parts.append('</div>')
        
        html_parts.append('</div>')
        html_parts.append('</div>')
        
        return ''.join(html_parts)
    
    async def generate_transcript(self, 
                                  channel: nextcord.TextChannel, 
                                  limit: Optional[int] = None,
                                  after: Optional[datetime] = None,
                                  before: Optional[datetime] = None) -> str:
        messages: List[nextcord.Message] = []
        async for message in channel.history(limit=limit, after=after, before=before):
            messages.append(message)
        
        messages.reverse()
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<title>Transcript - #{channel.name}</title>',
            self.css_styles,
            '</head>',
            '<body>',
            '<div class="transcript-container">',
            '<div class="header">',
            '<div class="header-icon">#</div>',
            '<div class="header-info">',
            f'<h1>#{self._escape_html(channel.name)}</h1>',
            f'<p>{len(messages)} messages • Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>',
            '</div>',
            '</div>',
            '<div class="messages-container">'
        ]
        
        current_date = None
        for message in messages:
            # Add date divider if needed
            message_date = message.created_at.date()
            if current_date != message_date:
                current_date = message_date
                html_parts.append('<div class="divider">')
                html_parts.append(f'<span class="divider-text">{message_date.strftime("%B %d, %Y")}</span>')
                html_parts.append('</div>')
            
            # Add message
            html_parts.append(self._generate_message_html(message))
        
        html_parts.extend([
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return ''.join(html_parts)
    
    async def generate_transcript_file(self,
                                       channel: nextcord.TextChannel,
                                       msg_limit: Optional[int] = None,
                                       after: Optional[datetime] = None,
                                       before: Optional[datetime] = None) -> Tuple[nextcord.File, List[nextcord.Message]]:
        if msg_limit is None:
            msg_limit = 1000
        else:
            if msg_limit > 1000:
                msg_limit = 1000
        messages: List[nextcord.Message] = []
        seen_message_ids = set()
        
        async for message in channel.history():
            if message.id not in seen_message_ids:
                messages.append(message)
                seen_message_ids.add(message.id)
        
        print(f"Messages fetched: {len(messages)} (unique)")
        messages.reverse()
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '<meta charset="UTF-8">',
            '<meta name="viewport" content="width=device-width, initial-scale=1.0">',
            f'<title>Transcript - #{channel.name}</title>',
            self.css_styles,
            '</head>',
            '<body>',
            '<div class="transcript-container">',
            '<div class="header">',
            '<div class="header-icon">#</div>',
            '<div class="header-info">',
            f'<h1>#{self._escape_html(channel.name)}</h1>',
            f'<p>{len(messages)} messages • Generated on {datetime.now().strftime("%B %d, %Y at %I:%M %p")}</p>',
            '</div>',
            '</div>',
            '<div class="messages-container">'
        ]
        
        current_date = None
        for message in messages:
            message_date = message.created_at.date()
            if current_date != message_date:
                current_date = message_date
                html_parts.append('<div class="divider">')
                html_parts.append(f'<span class="divider-text">{message_date.strftime("%B %d, %Y")}</span>')
                html_parts.append('</div>')
            
            html_parts.append(self._generate_message_html(message))
        
        html_parts.extend([
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        html_content = ''.join(html_parts)
        
        buffer = BytesIO(html_content.encode('utf-8'))
        buffer.seek(0)
        
        filename = f"transcript-{channel.name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.html"
        file = nextcord.File(buffer, filename=filename)
        
        return file, messages


async def create_channel_transcript(channel: nextcord.TextChannel, **kwargs) -> Tuple[nextcord.File, List[nextcord.Message]]:
    generator = TranscriptGenerator()
    return await generator.generate_transcript_file(channel, **kwargs)

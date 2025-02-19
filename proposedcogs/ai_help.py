import nextcord
from nextcord.ext import commands
from openai import OpenAI
import json

with open("config.json", "r") as file:
    config = json.load(file)

api_key = config["api_key"]

class AIHelp(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not hasattr(AIHelp, '_client'):
            AIHelp._client = OpenAI(
                api_key=api_key,
                base_url="https://openrouter.ai/api/v1"
            )
        self.client = AIHelp._client
        self.conversation_history = {}

    @commands.Cog.listener()
    async def on_ready(self):
        print("AI Help cog is ready")

    @commands.command(name="ask")
    async def ask_ai(self, ctx: commands.Context, *, question: str):
        server_info = {
            "server_id": ctx.guild.id,
            "server_name": ctx.guild.name,
            "member_count": ctx.guild.member_count,
            "boost_level": ctx.guild.premium_tier,
            "boost_count": ctx.guild.premium_subscription_count,
            "verification_level": str(ctx.guild.verification_level),
            "created_at": ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "owner": str(ctx.guild.owner),
            "owner_id": ctx.guild.owner_id,
            "roles": [[role.name, role.id] for role in ctx.guild.roles],
            "server_details": {
                "id": ctx.guild.id,
                "name": ctx.guild.name,
                "member_count": ctx.guild.member_count,
                "boost_level": ctx.guild.premium_tier,
                "boost_count": ctx.guild.premium_subscription_count,
                "verification_level": str(ctx.guild.verification_level),
                "created_at": ctx.guild.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "owner": str(ctx.guild.owner),
                "owner_id": ctx.guild.owner_id,
                "roles": [[role.name, role.id] for role in ctx.guild.roles],
            },
            "channel_name": ctx.channel.name,
            "channel_id": ctx.channel.id,
            "channel_type": str(ctx.channel.type),
            "channel_category": str(ctx.channel.category) if ctx.channel.category else "No Category",
            "channel_position": ctx.channel.position,
            "channel_nsfw": ctx.channel.is_nsfw(),
            "user_name": ctx.author.name,
            "user_id": ctx.author.id,
            "user_display_name": str(ctx.author.display_name),
            "user_roles": [role.name for role in ctx.author.roles],
            "user_joined_at": ctx.author.joined_at.strftime("%Y-%m-%d %H:%M:%S") if ctx.author.joined_at else None,
            "user_created_at": ctx.author.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "user_bot": ctx.author.bot,
            "message_id": ctx.message.id,
            "message_created_at": ctx.message.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "message_edited": ctx.message.edited_at.strftime("%Y-%m-%d %H:%M:%S") if ctx.message.edited_at else None,
        }

        if ctx.guild.id not in self.conversation_history:
            self.conversation_history[ctx.guild.id] = []

        system_prompt = f"""You are a helpful AI assistant for the Discord server '{server_info['server_name']}'. 
        You have access to the following detailed server information:

        SERVER INFORMATION:
        - Server ID: {server_info['server_id']}
        - Server Name: {server_info['server_name']}
        - Total Members: {server_info['member_count']}
        - Boost Level: {server_info['boost_level']}
        - Boost Count: {server_info['boost_count']}
        - Verification Level: {server_info['verification_level']}
        - Created On: {server_info['created_at']}
        - Server Owner: {server_info['owner']}
        - Available Roles: {', '.join(server_info['roles'])}
        - All Details Wrapped in a Map: {server_info['server_details']}

        CHANNEL INFORMATION:
        - Channel Name: {server_info['channel_name']}
        - Channel ID: {server_info['channel_id']}
        - Channel Type: {server_info['channel_type']}
        - Category: {server_info['channel_category']}
        - Position: {server_info['channel_position']}
        - NSFW: {server_info['channel_nsfw']}

        USER INFORMATION:
        - Username: {server_info['user_name']}
        - Display Name: {server_info['user_display_name']}
        - User ID: {server_info['user_id']}
        - Roles: {', '.join(server_info['user_roles'])}
        - Joined Server: {server_info['user_joined_at']}
        - Account Created: {server_info['user_created_at']}
        - Is Bot: {server_info['user_bot']}

        You can use this information to provide detailed responses about the server, channel, or user context.
        Always be helpful and accurate with the information provided."""

        messages = [
            {"role": "system", "content": system_prompt},
            *self.conversation_history[ctx.guild.id],
            {"role": "user", "content": question}
            ]

        try:
            async with ctx.typing():
                response = self.client.chat.completions.create(
                    model="nousresearch/hermes-3-llama-3.1-405b:free",
                    messages=messages,
                )

            ai_response = response.choices[0].message['content']

            self.conversation_history[ctx.guild.id].extend([
                {"role": "user", "content": question},
                {"role": "assistant", "content": ai_response}
            ])

            if len(self.conversation_history[ctx.guild.id]) > 20:
                self.conversation_history[ctx.guild.id] = self.conversation_history[ctx.guild.id][-20:]

            await ctx.reply(ai_response)

        except Exception as e:
            await ctx.reply(f"Sorry, I encountered an error: {str(e)}")

def setup(bot):
    bot.add_cog(AIHelp(bot))
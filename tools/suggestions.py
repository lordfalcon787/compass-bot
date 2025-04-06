import nextcord
from nextcord.ext import commands, application_checks
import asyncio
from utils.mongo_connection import MongoConnection
from typing import Optional


GREEN_CHECK = "<:green_check2:1291173532432203816>"
RED_X = "<:red_x2:1292657124832448584>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Misc"]
configuration = db["Configuration"]

class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Suggestions cog is ready")

    async def suggestions_config(self, interaction: nextcord.Interaction):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        suggestions_channel = config[f"suggestions"]
        suggestions_role = config[f"suggestion_role"]
        user_roles = [role.id for role in interaction.user.roles]
        no_suggestions_role = config.get(f"no_suggestions", 1)
        if guild_id not in suggestions_channel or guild_id not in suggestions_role:
            await interaction.response.send_message("Suggestions are not configured for this server.", ephemeral=True)
            return False
        elif suggestions_role[guild_id] not in user_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
        elif no_suggestions_role in user_roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return False
        return True
        

    @nextcord.slash_command(name="suggestion", description="Suggest a new feature for the server.")
    @application_checks.guild_only()
    async def suggestion(self, interaction: nextcord.Interaction):
        pass

    @suggestion.subcommand(name="approve", description="Approve a suggestion.")
    @application_checks.guild_only()
    @commands.check(suggestions_config)
    async def approve(self, interaction: nextcord.Interaction, suggestion: int, reason: Optional[str] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await interaction.response.send_message("No suggestions found.", ephemeral=True)
            return
        
        if str(suggestion) not in doc:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return
        elif reason is None:
            reason = "No reason provided."
        
        await interaction.response.defer(ephemeral=True)
        num = suggestion
        suggestion = doc[str(suggestion)]
        msg = interaction.guild.get_channel(suggestions_channel)
        msg = await msg.fetch_message(suggestion)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{num} Approved"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
        embed.set_footer(text=f"Approved by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await msg.edit(embed=embed)
        await interaction.send(f"Suggestion approved successfully for reason: {reason}", ephemeral=True)
        
        author_id = doc.get(f"{num}_author")
        if author_id:
            author = self.bot.get_user(int(author_id))
            if author:
                try:
                    await author.send(f"Your suggestion #{num} has been approved!\nReason: {reason}\nLink: {msg.jump_url}")
                except Exception as e:
                    print(f"Failed to send message to author: {e}")


    @suggestion.subcommand(name="implement", description="Mark a suggestion as implemented.")
    @application_checks.guild_only()
    @commands.check(suggestions_config)
    async def implemented(self, interaction: nextcord.Interaction, suggestion: int, reason: Optional[str] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await interaction.response.send_message("No suggestions found.", ephemeral=True)
            return
        
        if str(suggestion) not in doc:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return
        elif reason is None:
            reason = "No reason provided."
        
        await interaction.response.defer(ephemeral=True)
        num = suggestion
        suggestion = doc[str(suggestion)]
        msg = interaction.guild.get_channel(suggestions_channel)
        msg = await msg.fetch_message(suggestion)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{num} Implemented"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
        embed.set_footer(text=f"Implemented by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await msg.edit(embed=embed)
        await interaction.send(f"Suggestion marked as implemented successfully for reason: {reason}", ephemeral=True)
        author_id = doc.get(f"{num}_author")
        if author_id:
            author = self.bot.get_user(int(author_id))
            if author:
                try:
                    await author.send(f"Your suggestion #{num} has been implemented!\nReason: {reason}\nLink: {msg.jump_url}")
                except Exception as e:
                    print(f"Failed to send message to author: {e}")

    @suggestion.subcommand(name="deny", description="Deny a suggestion.")
    @application_checks.guild_only()
    @commands.check(suggestions_config)
    async def denied(self, interaction: nextcord.Interaction, suggestion: int, reason: Optional[str] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await interaction.response.send_message("No suggestions found.", ephemeral=True)
            return
        
        if str(suggestion) not in doc:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return
        elif reason is None:
            reason = "No reason provided."
        
        await interaction.response.defer(ephemeral=True)
        num = suggestion
        suggestion = doc[str(suggestion)]
        msg = interaction.guild.get_channel(suggestions_channel)
        msg = await msg.fetch_message(suggestion)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{num} Denied"
        embed.color = nextcord.Color.red()
        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
        embed.set_footer(text=f"Denied by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await msg.edit(embed=embed)
        await interaction.send(f"Suggestion denied successfully for reason: {reason}", ephemeral=True)
        author_id = doc.get(f"{num}_author")
        if author_id:
            author = self.bot.get_user(int(author_id))
            if author:
                try:
                    await author.send(f"Your suggestion #{num} has been denied.\nReason: {reason}\nLink: {msg.jump_url}")
                except Exception as e:
                    print(f"Failed to send message to author: {e}")

    @suggestion.subcommand(name="consider", description="Mark a suggestion as being considered.")
    @application_checks.guild_only()
    @commands.check(suggestions_config)
    async def considered(self, interaction: nextcord.Interaction, suggestion: int, reason: Optional[str] = None):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        suggestions_channel = config["suggestions"][guild_id]

        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await interaction.response.send_message("No suggestions found.", ephemeral=True)
            return
        
        if str(suggestion) not in doc:
            await interaction.response.send_message("Suggestion not found.", ephemeral=True)
            return
        elif reason is None:
            reason = "No reason provided."
        
        num = suggestion
        await interaction.response.defer(ephemeral=True)
        suggestion = doc[str(suggestion)]
        msg = interaction.guild.get_channel(suggestions_channel)
        msg = await msg.fetch_message(suggestion)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{num} Considered"
        embed.color = nextcord.Color.yellow()
        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
        embed.set_footer(text=f"Marked as considered by {interaction.user.name}", icon_url=interaction.user.avatar.url)
        await msg.edit(embed=embed)
        await interaction.send(f"Suggestion marked as being considered successfully for reason: {reason}", ephemeral=True)
        author_id = doc.get(f"{num}_author")
        if author_id:
            author = self.bot.get_user(int(author_id))
            if author:
                try:
                    await author.send(f"Your suggestion #{num} is being considered!\nReason: {reason}\nLink: {msg.jump_url}")
                except Exception as e:
                    print(f"Failed to send message to author: {e}")

    @suggestion.subcommand(name="suggest", description="Submit a new suggestion.")
    @application_checks.guild_only()
    @commands.check(suggestions_config)
    async def submit(self, interaction: nextcord.Interaction, suggestion: str):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(interaction.guild.id)
        roles = [role.id for role in interaction.user.roles]
        suggestions_channel = config["suggestions"]
        suggestions_role = config["suggestion_role"]

        if guild_id not in suggestions_channel or guild_id not in suggestions_role:
            await interaction.response.send_message("Suggestions are not configured for this server.", ephemeral=True)
            return
        
        suggestions_channel = config["suggestions"][guild_id]
        suggestions_role = config["suggestion_role"][guild_id]
        try:
            no_suggestions_role = config["no_suggestions"][guild_id]
        except:
            no_suggestions_role = 1
        

        if no_suggestions_role in roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        elif suggestions_role not in roles:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        await interaction.response.defer(ephemeral=True)
        try:
            last_suggestion = doc["last_suggestion"]
        except:
            last_suggestion = 0
        sugg_num = last_suggestion + 1
        sugg = suggestion 
        embed = nextcord.Embed(title=f"Suggestion #{sugg_num}", description=sugg)
        embed.set_author(name=interaction.user.name, icon_url=interaction.user.avatar.url)
        embed.color = nextcord.Color.blurple()
        channel = interaction.guild.get_channel(suggestions_channel)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {"last_suggestion": sugg_num, f"{sugg_num}": msg.id, f"{sugg_num}_author": interaction.user.id}}, upsert=True)
        await interaction.send(f"Suggestion #{sugg_num} submitted successfully!", ephemeral=True)

    async def command_deny(self, ctx):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(ctx.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        
        num = int(split[2])

        if len(split) == 3:
            reason = "No reason provided."
        else:
            reason = " ".join(split[3:])

        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await ctx.message.add_reaction(RED_X)
            return
        
        if str(num) not in doc:
            await ctx.message.add_reaction(RED_X)
            return
        
        old_num = num
        num = doc[str(num)]
        
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.fetch_message(num)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Denied"
        embed.color = nextcord.Color.red()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Denied by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await msg.edit(embed=embed)

        author_id = doc.get(f"{old_num}_author")
        if author_id:
            author = await ctx.guild.get_member(author_id)
            if author:
                try:
                    await author.send(f"Your suggestion #{old_num} has been denied.\nReason: {reason}\nLink: {msg.jump_url}")
                except:
                    pass

        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()

    async def command_approve(self, ctx):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(ctx.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        
        num = int(split[2])

        if len(split) == 3:
            reason = "No reason provided."
        else:
            reason = " ".join(split[3:])

        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await ctx.message.add_reaction(RED_X)
            return
        
        if str(num) not in doc:
            await ctx.message.add_reaction(RED_X)
            return

        old_num = num
        num = doc[str(num)]
        
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.fetch_message(num)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Approved"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Approved by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await msg.edit(embed=embed)
        author_id = doc.get(f"{old_num}_author")
        if author_id:
            author = await ctx.guild.get_member(author_id)
            if author:
                try:
                    await author.send(f"Your suggestion #{old_num} has been approved!\nReason: {reason}\nLink: {msg.jump_url}")
                except:
                    pass

        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()

    async def command_implemented(self, ctx):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(ctx.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        
        num = int(split[2])

        if len(split) == 3:
            reason = "No reason provided."
        else:
            reason = " ".join(split[3:])

        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await ctx.message.add_reaction(RED_X)
            return
        
        if str(num) not in doc:
            await ctx.message.add_reaction(RED_X)
            return

        old_num = num
        num = doc[str(num)]
        
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.fetch_message(num)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Implemented"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Marked as implemented by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await msg.edit(embed=embed)
        author_id = doc.get(f"{old_num}_author")
        if author_id:
            author = await ctx.guild.get_member(author_id)
            if author:
                try:
                    await author.send(f"Your suggestion #{old_num} has been implemented!\nReason: {reason}\nLink: {msg.jump_url}")
                except:
                    pass

        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()

    async def command_considered(self, ctx):
        config = configuration.find_one({"_id": "config"})
        guild_id = str(ctx.guild.id)
        suggestions_channel = config["suggestions"][guild_id]
        split = ctx.message.content.split(" ")
        if len(split) <= 2:
            await ctx.message.add_reaction(RED_X)
            return
        
        num = int(split[2])

        if len(split) == 3:
            reason = "No reason provided."
        else:
            reason = " ".join(split[3:])

        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            await ctx.message.add_reaction(RED_X)
            return
        
        if str(num) not in doc:
            await ctx.message.add_reaction(RED_X)
            return

        old_num = num
        num = doc[str(num)]
        
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.fetch_message(num)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Considered"
        embed.color = nextcord.Color.yellow()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Marked as considered by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        await msg.edit(embed=embed)
        author_id = doc.get(f"{old_num}_author")
        if author_id:
            author = await ctx.guild.get_member(author_id)
            if author:
                try:
                    await author.send(f"Your suggestion #{old_num} is being considered!\nReason: {reason}\nLink: {msg.jump_url}")
                except:
                    pass

        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()

    @commands.command(name="suggest", aliases=["suggestions", "suggestion"])
    async def suggest(self, ctx: commands.Context, *, suggestion: str):
        roles = [role.id for role in ctx.author.roles]
        commands = ["deny", "approve", "implement", "consider"]
        config = configuration.find_one({"_id": "config"})
        suggestions_channel = config["suggestions"]
        suggestions_role = config["suggestion_role"]
        guild_id = str(ctx.guild.id)
        try:
            no_suggestions_role = config["no_suggestions"][guild_id]
        except:
            no_suggestions_role = 1

        if guild_id not in suggestions_channel or guild_id not in suggestions_role:
            await ctx.reply("Suggestions are not configured for this server.", mention_author=False)
            await ctx.message.add_reaction(RED_X)
            return
        
        suggestions_channel = config["suggestions"][guild_id]
        suggestions_role = config["suggestion_role"][guild_id]
        

        if no_suggestions_role in roles:
            await ctx.message.add_reaction(RED_X)
            return
        elif suggestions_role not in roles:
            await ctx.message.add_reaction(RED_X)
            return
        
        split = ctx.message.content.split(" ")
        if split[1].lower() in commands:
            if not ctx.author.guild_permissions.administrator:
                await ctx.message.add_reaction(RED_X)
                return
            if split[1].lower() == "deny":
                await self.command_deny(ctx)
            elif split[1].lower() == "approve":
                await self.command_approve(ctx)
            elif split[1].lower() == "implement":
                await self.command_implemented(ctx)
            elif split[1].lower() == "consider":
                await self.command_considered(ctx)
            return
        
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        try:
            last_suggestion = doc["last_suggestion"]
        except:
            last_suggestion = 0
        sugg_num = last_suggestion + 1
        sugg = suggestion 
        embed = nextcord.Embed(title=f"Suggestion #{sugg_num}", description=sugg)
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar.url)
        embed.color = nextcord.Color.blurple()
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.send(embed=embed)
        await msg.add_reaction("⬆️")
        await msg.add_reaction("⬇️")
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {"last_suggestion": sugg_num, f"{sugg_num}": msg.id, f"{sugg_num}_author": ctx.author.id}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: nextcord.RawReactionActionEvent):
        try:
            msg_id = payload.message_id
            channel_id = payload.channel_id
            channel = self.bot.get_channel(channel_id)
            msg = await channel.fetch_message(msg_id)
        except:
            return
        
        if payload.user_id == self.bot.user.id:
            return
        elif not msg.embeds:
            return
        elif not msg.embeds[0].title:
            return
        elif msg.author.id != self.bot.user.id:
            return
        elif not msg.embeds[0].title.startswith("Suggestion"):
            return
        
        if payload.emoji.name == "⬆️" or payload.emoji.name == "⬇️":
            try:
                await msg.create_thread(name="Discuss")
            except:
                return
            try:
                async with asyncio.timeout(10):
                    async for message in msg.channel.history(limit=10):
                        if "Discuss" in message.content:
                            await message.delete()
                            break
            except asyncio.TimeoutError:
                return
def setup(bot):
    bot.add_cog(Suggestions(bot))
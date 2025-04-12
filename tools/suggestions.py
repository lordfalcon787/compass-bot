import aiohttp
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

class View(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

        self.agree = nextcord.ui.Button(label="Agree [0]", style=nextcord.ButtonStyle.green, custom_id="agree_suggestions")
        self.disagree = nextcord.ui.Button(label="Disagree [0]", style=nextcord.ButtonStyle.red, custom_id="disagree_suggestions")
        self.agree.callback = self.agree_callback
        self.disagree.callback = self.disagree_callback
        self.add_item(self.agree)
        self.add_item(self.disagree)
        self.votes = nextcord.ui.Button(label="Votes", style=nextcord.ButtonStyle.blurple, custom_id="votes_suggestions")
        self.votes.callback = self.votes_callback
        self.add_item(self.votes)

    async def votes_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            return
        suggestion_num = interaction.message.embeds[0].title.split("#")[1]
        suggestion_num = int(suggestion_num.split(" ")[0])
        new_doc = doc[str(suggestion_num)]
        upvotes = new_doc.get("upvotes", [])
        downvotes = new_doc.get("downvotes", [])
        embed = nextcord.Embed(
            title=f"Suggestion #{suggestion_num} Votes",
            color=nextcord.Color.blurple()
        )
        
        upvote_users = []
        downvote_users = []
        
        for user_id in upvotes:
            try:
                upvote_users.append(f"<@{user_id}>")
            except:
                upvote_users.append(f"Unknown User ({user_id})")
        
        for user_id in downvotes:
            try:
                downvote_users.append(f"<@{user_id}>")
            except:
                downvote_users.append(f"Unknown User ({user_id})")
        
        total_pages = max(
            (len(upvote_users) + 9) // 10,
            (len(downvote_users) + 9) // 10
        ) or 1

        response = None
        
        class VotesView(nextcord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.current_page = 1
                self.update_buttons()
            
            def update_buttons(self):
                self.prev_button.disabled = self.current_page <= 1
                self.next_button.disabled = self.current_page >= total_pages
            
            def update_embed(self):
                embed.clear_fields()
                
                start_idx = (self.current_page - 1) * 10
                
                upvotes_for_page = upvote_users[start_idx:start_idx+10] if start_idx < len(upvote_users) else []
                if upvotes_for_page:
                    upvotes_display = "\n".join(upvotes_for_page)
                    embed.add_field(
                        name=f"Agree [{len(upvote_users)}]",
                        value=upvotes_display,
                        inline=False
                    )
                else:
                    if len(upvote_users) > 0:
                        embed.add_field(name=f"Agree [{len(upvote_users)}]", 
                                       value="No votes on this page", 
                                       inline=False)
                    else:
                        embed.add_field(name="Agree [0]", 
                                       value="No votes", 
                                       inline=False)
                
                downvotes_for_page = downvote_users[start_idx:start_idx+10] if start_idx < len(downvote_users) else []
                if downvotes_for_page:
                    downvotes_display = "\n".join(downvotes_for_page)
                    embed.add_field(
                        name=f"Disagree [{len(downvote_users)}]",
                        value=downvotes_display,
                        inline=False
                    )
                else:
                    if len(downvote_users) > 0:
                        embed.add_field(name=f"Disagree [{len(downvote_users)}]", 
                                       value="No votes on this page", 
                                       inline=False)
                    else:
                        embed.add_field(name="Disagree [0]", 
                                       value="No votes", 
                                       inline=False)
                
                embed.set_footer(text=f"Page {self.current_page}/{total_pages}")
                
                return embed
            
            @nextcord.ui.button(label="◀ Previous", style=nextcord.ButtonStyle.blurple, custom_id="prev_page")
            async def prev_button(self, button, interaction):
                nonlocal response
                if self.current_page > 1:
                    self.current_page -= 1
                    self.update_buttons()
                    await response.edit(embed=self.update_embed(), view=self)
                else:
                    await interaction.response.defer()
            
            @nextcord.ui.button(label="Next ▶", style=nextcord.ButtonStyle.blurple, custom_id="next_page")
            async def next_button(self, button, interaction):
                nonlocal response
                if self.current_page < total_pages:
                    self.current_page += 1
                    self.update_buttons()
                    await response.edit(embed=self.update_embed(), view=self)
                else:
                    await interaction.response.defer()
        
        votes_view = VotesView()
        response = await interaction.followup.send(embed=votes_view.update_embed(), view=votes_view, ephemeral=True)

    async def agree_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            return
        suggestion_num = interaction.message.embeds[0].title.split("#")[1]
        suggestion_num = int(suggestion_num.split(" ")[0])
        new_doc = doc[str(suggestion_num)]
        try:
            upvotes = new_doc.get("upvotes", [])
            downvotes = new_doc.get("downvotes", [])
        except:
            upvotes = []
            downvotes = []
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
            new_doc["upvotes"] = upvotes
            collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {f"{suggestion_num}": new_doc}}, upsert=True)
            view = View()
            view.agree.label = f"Agree [{len(upvotes)}]"
            view.disagree.label = f"Disagree [{len(downvotes)}]"
            await interaction.message.edit(view=view)
            await interaction.send("You have removed your vote to agree.", ephemeral=True)
            return
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)
        new_doc["upvotes"] = upvotes + [interaction.user.id]
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {f"{suggestion_num}": new_doc}}, upsert=True)
        view = View()
        view.agree.label = f"Agree [{len(upvotes) + 1}]"
        view.disagree.label = f"Disagree [{len(downvotes)}]"
        await interaction.message.edit(view=view) 
        embed = nextcord.Embed(title="You have voted to agree.", color=nextcord.Color.green())
        await interaction.followup.send(embed=embed, ephemeral=True)
        if not interaction.message.thread:
            await interaction.message.create_thread(name="Suggestion Discussion")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://google.com") as response:
                    if response.status == 200:
                        async with asyncio.timeout(10):
                            async for message in interaction.message.channel.history(limit=10):
                                if "Suggestion Discussion" in message.content:
                                    await message.delete()
                                    break
                    else:
                        return

    async def disagree_callback(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild_id = str(interaction.guild.id)
        doc = collection.find_one({"_id": f"suggestions_{guild_id}"})
        if doc is None:
            return
        suggestion_num = interaction.message.embeds[0].title.split("#")[1]
        suggestion_num = int(suggestion_num.split(" ")[0])
        new_doc = doc[str(suggestion_num)]
        try:
            upvotes = new_doc.get("upvotes", [])
            downvotes = new_doc.get("downvotes", [])
        except:
            upvotes = []
            downvotes = []
        if interaction.user.id in downvotes:
            downvotes.remove(interaction.user.id)
            new_doc["downvotes"] = downvotes
            collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {f"{suggestion_num}": new_doc}}, upsert=True)
            view = View()
            view.agree.label = f"Agree [{len(upvotes)}]"
            view.disagree.label = f"Disagree [{len(downvotes)}]"
            await interaction.message.edit(view=view)
            await interaction.send("You have removed your vote to disagree.", ephemeral=True)
            return
        if interaction.user.id in upvotes:
            upvotes.remove(interaction.user.id)
        new_doc["downvotes"] = downvotes + [interaction.user.id]
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {f"{suggestion_num}": new_doc}}, upsert=True)
        view = View()
        view.agree.label = f"Agree [{len(upvotes)}]"
        view.disagree.label = f"Disagree [{len(downvotes) + 1}]"
        await interaction.message.edit(view=view)
        embed = nextcord.Embed(title="You have voted to disagree.", color=nextcord.Color.green())
        await interaction.followup.send(embed=embed, ephemeral=True)
        if not interaction.message.thread:
            await interaction.message.create_thread(name="Suggestion Discussion")
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://google.com") as response:
                    if response.status == 200:
                        async with asyncio.timeout(10):
                            async for message in interaction.message.channel.history(limit=10):
                                if "Suggestion Discussion" in message.content:
                                    await message.delete()
                                    break
                    else:
                        return

        
class Suggestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Suggestions cog is ready")
        self.bot.add_view(View())

    async def disable_view(self, message: nextcord.Message):
        doc = collection.find_one({"_id": f"suggestions_{message.guild.id}"})
        if doc is None:
            return
        suggestion_num = message.embeds[0].title.split("#")[1]
        suggestion_num = int(suggestion_num.split(" ")[0])
        new_doc = doc[str(suggestion_num)]
        upvotes = new_doc.get("upvotes", 0)
        downvotes = new_doc.get("downvotes", 0)
        new_doc["upvotes"] = upvotes
        new_doc["downvotes"] = downvotes
        view = View()
        view.agree.label = f"Agree [{upvotes}]"
        view.disagree.label = f"Disagree [{downvotes}]"
        view.agree.disabled = True
        view.disagree.disabled = True
        return view


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
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://google.com") as response:
                if response.status == 200:
                    async with asyncio.timeout(10):
                        msg = await msg.fetch_message(suggestion.get("message_id"))
                        embed = msg.embeds[0]
                        embed.title = f"Suggestion #{num} Approved"
                        embed.color = nextcord.Color.green()
                        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
                        embed.set_footer(text=f"Approved by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                        view = await self.disable_view(msg)
                        await msg.edit(embed=embed, view=view)
                        await interaction.send(f"Suggestion approved successfully for reason: {reason}", ephemeral=True)
                else:
                    await interaction.send("Failed to fetch message.", ephemeral=True)
        
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
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://google.com") as response:
                if response.status == 200:
                    async with asyncio.timeout(10):
                        msg = await msg.fetch_message(suggestion.get("message_id"))
                        embed = msg.embeds[0]
                        embed.title = f"Suggestion #{num} Implemented"
                        embed.color = nextcord.Color.green()
                        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
                        embed.set_footer(text=f"Implemented by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                        view = await self.disable_view(msg)
                        await msg.edit(embed=embed, view=view)
                        await interaction.send(f"Suggestion marked as implemented successfully for reason: {reason}", ephemeral=True)
                else:
                    await interaction.send("Failed to fetch message.", ephemeral=True)
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
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://google.com") as response:
                if response.status == 200:
                    async with asyncio.timeout(10):
                        msg = await msg.fetch_message(suggestion.get("message_id"))
                        embed = msg.embeds[0]
                        embed.title = f"Suggestion #{num} Denied"
                        embed.color = nextcord.Color.red()
                        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
                        embed.set_footer(text=f"Denied by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                        view = await self.disable_view(msg)
                        await msg.edit(embed=embed, view=view)
                        await interaction.send(f"Suggestion denied successfully for reason: {reason}", ephemeral=True)
                else:
                    await interaction.send("Failed to fetch message.", ephemeral=True)
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
        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://google.com") as response:
                if response.status == 200:
                    async with asyncio.timeout(10):
                        msg = await msg.fetch_message(suggestion.get("message_id"))
                        embed = msg.embeds[0]
                        embed.title = f"Suggestion #{num} Considered"
                        embed.color = nextcord.Color.yellow()
                        embed.add_field(name=f"Reason from {interaction.user.name}", value=reason, inline=False)
                        embed.set_footer(text=f"Marked as considered by {interaction.user.name}", icon_url=interaction.user.avatar.url)
                        view = await self.disable_view(msg)
                        await msg.edit(embed=embed, view=view)
                        await interaction.send(f"Suggestion marked as being considered successfully for reason: {reason}", ephemeral=True)
                else:
                    await interaction.send("Failed to fetch message.", ephemeral=True)
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
        msg = await channel.send(embed=embed, view=View())
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {"last_suggestion": sugg_num, f"{sugg_num}.message_id": msg.id, f"{sugg_num}_author": interaction.user.id}}, upsert=True)
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
        msg = await channel.fetch_message(num.get("message_id"))
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Denied"
        embed.color = nextcord.Color.red()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Denied by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        view = await self.disable_view(msg)
        await msg.edit(embed=embed, view=view)

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
        msg = await channel.fetch_message(num.get("message_id"))
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Approved"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Approved by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        view = await self.disable_view(msg)
        await msg.edit(embed=embed, view=view)
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
        msg = await channel.fetch_message(num.get("message_id"))
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Implemented"
        embed.color = nextcord.Color.green()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Marked as implemented by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        view = await self.disable_view(msg)
        await msg.edit(embed=embed, view=view)
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
        num = num.get("message_id")
        
        channel = ctx.guild.get_channel(suggestions_channel)
        msg = await channel.fetch_message(num)
        embed = msg.embeds[0]
        embed.title = f"Suggestion #{old_num} Considered"
        embed.color = nextcord.Color.yellow()
        embed.add_field(name=f"Reason from {ctx.author.name}", value=reason, inline=False)
        embed.set_footer(text=f"Marked as considered by {ctx.author.name}", icon_url=ctx.author.avatar.url)
        view = await self.disable_view(msg)
        await msg.edit(embed=embed, view=view)
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
        msg = await channel.send(embed=embed, view=View())
        collection.update_one({"_id": f"suggestions_{guild_id}"}, {"$set": {"last_suggestion": sugg_num, f"{sugg_num}.message_id": msg.id, f"{sugg_num}_author": ctx.author.id}}, upsert=True)
        await ctx.message.add_reaction(GREEN_CHECK)
        await asyncio.sleep(2)
        await ctx.message.delete()
def setup(bot):
    bot.add_cog(Suggestions(bot))
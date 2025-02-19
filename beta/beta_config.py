import nextcord
from nextcord.ext import commands, application_checks

from beta_mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
configuration = db["Configuration"]
credit_config = db["Credit"]

DOT = "<a:golddot:1303833388410601522>"
CHANNEL = "<:channel:1319130208896421889>"

class View(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        button = nextcord.ui.Button(label="Home", style=nextcord.ButtonStyle.primary, emoji="🏠")
        button.callback = self.home
        self.add_item(button)
        self.bot = bot

    async def home(self, interaction: nextcord.Interaction):
        await interaction.response.defer(ephemeral=True)
        embed = nextcord.Embed(
            title="Bot Configuration",
            description="Please select what you would like to configure below.",
            color=nextcord.Color.blue()
        )

        view = nextcord.ui.View()
        original_interaction = interaction
        
        payout_button = nextcord.ui.Button(label="Payout System", style=nextcord.ButtonStyle.primary, emoji="💵")
        ar_button = nextcord.ui.Button(label="Auto-Responder", style=nextcord.ButtonStyle.primary, emoji="💬") 
        highlight_button = nextcord.ui.Button(label="Highlight", style=nextcord.ButtonStyle.primary, emoji="🔍")
        auction_button = nextcord.ui.Button(label="Auction", style=nextcord.ButtonStyle.primary, emoji="💰")
        auto_lock_button = nextcord.ui.Button(label="Auto-Lock", style=nextcord.ButtonStyle.primary, emoji="🔒")
        suggestions_button = nextcord.ui.Button(label="Suggestions", style=nextcord.ButtonStyle.primary, emoji="🎗")
        mafia_logs_button = nextcord.ui.Button(label="Mafia Logs", style=nextcord.ButtonStyle.primary, emoji="🔪")
        counting_button = nextcord.ui.Button(label="Counting", style=nextcord.ButtonStyle.primary, emoji="💯")
        strike_button = nextcord.ui.Button(label="Strikes", style=nextcord.ButtonStyle.primary, emoji="🔨")
        utility_button = nextcord.ui.Button(label="Utility", style=nextcord.ButtonStyle.primary, emoji="🧰")
        staff_list_button = nextcord.ui.Button(label="Staff List", style=nextcord.ButtonStyle.primary, emoji="🪄")
        pcms_button = nextcord.ui.Button(label="PCMS", style=nextcord.ButtonStyle.primary, emoji="💳")
        afk_button = nextcord.ui.Button(label="AFK", style=nextcord.ButtonStyle.primary, emoji="💤")

        async def payout_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").payout_config(original_interaction)

        async def ar_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").ar_config(original_interaction)

        async def highlight_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").highlight_config(original_interaction)

        async def auction_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").auction_config(original_interaction)

        async def auto_lock_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").auto_lock(original_interaction)

        async def suggestions_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").suggestions_config(original_interaction)

        async def mafia_logs_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").mafia_logs_config(original_interaction)

        async def counting_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").counting_config(original_interaction)

        async def strike_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").strike_config(original_interaction)

        async def utility_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").utility_config(original_interaction)

        async def staff_list_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").staff_list_config(original_interaction)

        async def pcms_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").pcms_config(original_interaction)

        async def afk_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.bot.get_cog("Config").afk_config(original_interaction)

        payout_button.callback = payout_callback
        ar_button.callback = ar_callback
        highlight_button.callback = highlight_callback
        auction_button.callback = auction_callback
        auto_lock_button.callback = auto_lock_callback
        suggestions_button.callback = suggestions_callback
        mafia_logs_button.callback = mafia_logs_callback
        counting_button.callback = counting_callback
        strike_button.callback = strike_callback
        utility_button.callback = utility_callback
        staff_list_button.callback = staff_list_callback
        pcms_button.callback = pcms_callback
        afk_button.callback = afk_callback
        view.add_item(payout_button)
        view.add_item(ar_button)
        view.add_item(highlight_button)
        view.add_item(auction_button)
        view.add_item(auto_lock_button)
        view.add_item(suggestions_button)
        view.add_item(mafia_logs_button)
        view.add_item(counting_button)
        view.add_item(strike_button)
        view.add_item(utility_button)
        view.add_item(staff_list_button)
        view.add_item(pcms_button)
        view.add_item(afk_button)
        await interaction.message.edit(embed=embed, view=view)

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Config cog is ready.")

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: nextcord.Role):
        guild = str(role.guild.id)
        role_id = role.id
        doc = configuration.find_one({"_id": "config"})
        for key in doc.keys():
            item = doc[key]
            if isinstance(item, dict) and guild in item:
                stuff = item[guild]
                try:
                    if isinstance(stuff, list):
                        stuff = [x for x in stuff if x != role_id and x != str(role_id)]
                    elif isinstance(stuff, dict):
                        stuff.pop(str(role_id), None)
                    elif stuff == role_id or stuff == str(role_id):
                        item.pop(guild)
                    if guild in item and not item[guild]:
                        item.pop(guild)
                    configuration.update_one({"_id": "config"}, {"$set": {key: item}})
                except (ValueError, KeyError):
                    continue
        doc = configuration.find_one({"_id": "ar_config"})
        for key in doc.keys():
            item = doc[key]
            if isinstance(item, dict) and guild in item:
                stuff = item[guild]
                try:
                    if isinstance(stuff, list):
                        stuff = [x for x in stuff if x != role_id and x != str(role_id)]
                    elif isinstance(stuff, dict):
                        stuff.pop(str(role_id), None)
                    elif stuff == role_id or stuff == str(role_id):
                        stuff = None
                    item[guild] = stuff
                    configuration.update_one({"_id": "ar_config"}, {"$set": {key: item}})
                except (ValueError, KeyError):
                    continue
            

    @nextcord.slash_command(name="config", description="Configure the bot settings for the server.")
    @application_checks.guild_only()
    async def config(self, interaction: nextcord.Interaction):
        if interaction.user.id != 1166134423146729563:
            return
        if not interaction.user.guild_permissions.administrator:
            embed = nextcord.Embed(
                title="Invalid Permissions",
                description="You do not have the required permissions to use this command.",
                color=nextcord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        await interaction.response.defer()
        embed = nextcord.Embed(
            title="Bot Configuration",
            description="Please select what you would like to configure below.",
            color=nextcord.Color.blue()
        )

        view = nextcord.ui.View()
        original_interaction = interaction
        
        payout_button = nextcord.ui.Button(label="Payout System", style=nextcord.ButtonStyle.primary, emoji="💵")
        ar_button = nextcord.ui.Button(label="Auto-Responder", style=nextcord.ButtonStyle.primary, emoji="💬") 
        highlight_button = nextcord.ui.Button(label="Highlight", style=nextcord.ButtonStyle.primary, emoji="🔍")
        auction_button = nextcord.ui.Button(label="Auction", style=nextcord.ButtonStyle.primary, emoji="💰")
        auto_lock_button = nextcord.ui.Button(label="Auto-Lock", style=nextcord.ButtonStyle.primary, emoji="🔒")
        suggestions_button = nextcord.ui.Button(label="Suggestions", style=nextcord.ButtonStyle.primary, emoji="🎗")
        mafia_logs_button = nextcord.ui.Button(label="Mafia Logs", style=nextcord.ButtonStyle.primary, emoji="🔪")
        counting_button = nextcord.ui.Button(label="Counting", style=nextcord.ButtonStyle.primary, emoji="💯")
        strike_button = nextcord.ui.Button(label="Strikes", style=nextcord.ButtonStyle.primary, emoji="🔨")
        utility_button = nextcord.ui.Button(label="Utility", style=nextcord.ButtonStyle.primary, emoji="🧰")
        staff_list_button = nextcord.ui.Button(label="Staff List", style=nextcord.ButtonStyle.primary, emoji="🪄")
        pcms_button = nextcord.ui.Button(label="PCMS", style=nextcord.ButtonStyle.primary, emoji="💳")
        afk_button = nextcord.ui.Button(label="AFK", style=nextcord.ButtonStyle.primary, emoji="💤")

        async def payout_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.payout_config(interaction)

        async def ar_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.ar_config(interaction)

        async def highlight_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.highlight_config(interaction)

        async def auction_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.auction_config(interaction)

        async def auto_lock_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.auto_lock(interaction)
        
        async def suggestions_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.suggestions_config(interaction)

        async def mafia_logs_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.mafia_logs_config(interaction)

        async def counting_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.counting_config(interaction)

        async def strike_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.strike_config(interaction)

        async def utility_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.utility_config(interaction)

        async def staff_list_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.staff_list_config(interaction)

        async def pcms_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.pcms_config(interaction)

        async def afk_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await self.afk_config(interaction)

        payout_button.callback = payout_callback
        ar_button.callback = ar_callback
        highlight_button.callback = highlight_callback
        auction_button.callback = auction_callback
        auto_lock_button.callback = auto_lock_callback
        suggestions_button.callback = suggestions_callback
        mafia_logs_button.callback = mafia_logs_callback
        counting_button.callback = counting_callback
        strike_button.callback = strike_callback
        utility_button.callback = utility_callback
        staff_list_button.callback = staff_list_callback
        pcms_button.callback = pcms_callback
        afk_button.callback = afk_callback
        view.add_item(payout_button)
        view.add_item(ar_button)
        view.add_item(highlight_button)
        view.add_item(auction_button)
        view.add_item(auto_lock_button)
        view.add_item(suggestions_button)
        view.add_item(mafia_logs_button)
        view.add_item(counting_button)
        view.add_item(strike_button)
        view.add_item(utility_button)
        view.add_item(staff_list_button)
        view.add_item(pcms_button)
        view.add_item(afk_button)
        await interaction.send(embed=embed, view=view, ephemeral=False)

    async def afk_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="AFK Configuration",
            description="Configure the AFK system for the server.",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        original_interaction = interaction
        doc = configuration.find_one({"_id": "config"})
        afk_access = doc["afk"]
        if guild in afk_access:
            embed.add_field(name="AFK Allowed", value=", ".join(f"<@&{role}>" for role in afk_access[guild]), inline=True)
        else:
            embed.add_field(name="AFK Allowed", value="None.", inline=True)
        
        async def update_config_embed(interaction: nextcord.Interaction):
            await interaction.response.defer(ephemeral=True)
            doc = configuration.find_one({"_id": "config"})
            afk_access = doc["afk"]
            embed = nextcord.Embed(
                title="AFK Configuration",
                description="Configure the AFK system for the server.",
                color=nextcord.Color.blue()
            )
            if guild in afk_access:
                embed.add_field(name="AFK Allowed", value=", ".join(f"<@&{role}>" for role in afk_access[guild]), inline=True)
            else:
                embed.add_field(name="AFK Allowed", value="None.", inline=True)
            await original_interaction.message.edit(embed=embed)

        view = View(self.bot)

        async def update_roles(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select roles",
                min_values=1,
                max_values=25
            )
            view = nextcord.ui.View()
            async def role_select_callback(interaction: nextcord.Interaction):
                selected_roles = [role.id for role in role_select.values]
                doc = configuration.find_one({"_id": "config"})
                afk_access = doc["afk"]
                if guild not in afk_access:
                    afk_access = []
                else:
                    afk_access = afk_access[guild]
                for role_id in selected_roles:
                    if role_id in afk_access:
                        afk_access.remove(role_id)
                    else:
                        afk_access.append(role_id)
                configuration.update_one({"_id": "config"}, {"$set": {f"afk.{guild}": afk_access}}, upsert=True)
                await update_config_embed(interaction)
                try:
                    await interaction.response.send_message("AFK roles updated.", ephemeral=True)
                except:
                    await interaction.send("AFK roles updated.", ephemeral=True)

            role_select.callback = role_select_callback
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        update_button = nextcord.ui.Button(label="Update Roles", style=nextcord.ButtonStyle.primary, emoji="💤")
        update_button.callback = update_roles
        view.add_item(update_button)
        await interaction.message.edit(embed=embed, view=view)

    async def pcms_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="PCMS Configuration", 
            description="For a user to be able to use the PCMS system, they must have their user ID in the topic of their private channel.",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        pcms_roles = doc["pcms"]
        pcms_reqs = doc["pcms_reqs"]
        original_interaction = interaction
        if guild in pcms_roles:
            guild_roles = pcms_roles[guild]
            value = ""
            for key in guild_roles.keys():
                value = f"{value}\n<@&{key}> - `{guild_roles[key]}`"
            embed.add_field(name="Roles and Values", value=value, inline=True)
        else:
            embed.add_field(name="Roles and Values", value="None.", inline=True)

        if guild in pcms_reqs:
            guild_reqs = pcms_reqs[guild]
            value = ", ".join(f"<@&{role}>" for role in guild_reqs)
            embed.add_field(name="Requirements", value=value, inline=True)
        else:
            embed.add_field(name="Requirements", value="None.", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            pcms_roles = doc["pcms"]
            pcms_reqs = doc["pcms_reqs"]
            embed = nextcord.Embed(
                title="PCMS Configuration",
                description="For a user to be able to use the PCMS system, they must have their user ID in the topic of their private channel.",
                color=nextcord.Color.blue()
            )
            if guild in pcms_roles:
                guild_roles = pcms_roles[guild]
                value = ""
                for key in guild_roles.keys():
                    value = f"{value}\n<@&{key}> - `{guild_roles[key]}`"
                embed.add_field(name="Roles and Values", value=value, inline=True)
            else:
                embed.add_field(name="Roles and Values", value="None.", inline=True)
            if guild in pcms_reqs:
                guild_reqs = pcms_reqs[guild]
                value = ""
                for role in guild_reqs:
                    if value == "":
                        value = f"<@&{role}>"
                    else:
                        value = f"{value}, <@&{role}>"
                embed.add_field(name="Requirements", value=value, inline=True)
            else:
                embed.add_field(name="Requirements", value="None.", inline=True)
            await interaction.message.edit(embed=embed)

        class AmountModal(nextcord.ui.Modal):
            def __init__(self, role_id, original_interaction, update_embed):
                super().__init__(
                    "Enter Amount",
                    timeout=300,
                )
                self.role_id = role_id
                self.original_interaction = original_interaction
                self.update_embed = update_embed
                self.amount = nextcord.ui.TextInput(
                    label="Amount",
                    placeholder="Enter the number of members they can add",
                    min_length=1,
                    max_length=2,
                )
                self.add_item(self.amount)

            async def callback(self, interaction: nextcord.Interaction):
                try:
                    amount = int(self.amount.value)
                except ValueError:
                    await interaction.response.send_message("Please enter a valid number.", ephemeral=True)
                    return

                if amount <= 0:
                    await interaction.response.send_message("Please enter a positive number, greater than 0.", ephemeral=True)
                    return

                guild = str(interaction.guild.id)
                doc = configuration.find_one({"_id": "config"})
                pcms_roles = doc.get("pcms", {})
                
                if guild not in pcms_roles:
                    pcms_roles[guild] = {}
                
                pcms_roles[guild][str(self.role_id)] = amount
                
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {"pcms": pcms_roles}}
                )
                
                await interaction.response.send_message(f"Updated role amount successfully!", ephemeral=True)
                await update_config_embed(original_interaction)

        view = View(self.bot)

        async def roles_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select a role",
                min_values=1,
                max_values=1
            )

            async def role_select_callback(interaction: nextcord.Interaction):
                modal = AmountModal(role_select.values[0].id, original_interaction, update_config_embed)
                await interaction.response.send_modal(modal)

            role_select.callback = role_select_callback
            role_view = nextcord.ui.View()
            role_view.add_item(role_select)
            await interaction.response.send_message("Select a role to set the amount for:", view=role_view, ephemeral=True)

        async def reqs_callback(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return

            role_select = nextcord.ui.RoleSelect(
                placeholder="Select roles",
                min_values=1,
                max_values=25
            )

            async def req_role_select_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                doc = configuration.find_one({"_id": "config"})
                pcms_reqs = doc.get("pcms_reqs", [])
                guild = str(interaction.guild.id)
                
                if guild not in pcms_reqs:
                    pcms_reqs[guild] = []
                
                selected_role_ids = pcms_reqs[guild]
                for role in role_select.values:
                    if role.id in selected_role_ids:
                        selected_role_ids.remove(role.id)
                    else:
                        selected_role_ids.append(role.id)
                pcms_reqs[guild] = selected_role_ids
                
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {"pcms_reqs": pcms_reqs}}
                )
                
                await interaction.followup.send("Updated requirements successfully!", ephemeral=True)
                await update_config_embed(original_interaction)

            role_select.callback = req_role_select_callback
            role_view = nextcord.ui.View()
            role_view.add_item(role_select)
            await interaction.response.send_message("Select roles to toggle as requirements:", view=role_view, ephemeral=True)

        async def disable_pcms(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"pcms.{guild}": "", f"pcms_reqs.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("PCMS module disabled for this server.", ephemeral=True)

        roles_button = nextcord.ui.Button(label="Edit Roles", style=nextcord.ButtonStyle.primary)
        reqs_button = nextcord.ui.Button(label="Edit Requirements", style=nextcord.ButtonStyle.primary)
        disable_button = nextcord.ui.Button(label="Disable Module", style=nextcord.ButtonStyle.danger, emoji="❌")
        disable_button.callback = disable_pcms
        roles_button.callback = roles_callback
        reqs_button.callback = reqs_callback

        view.add_item(roles_button)
        view.add_item(reqs_button)
        view.add_item(disable_button)
        await interaction.message.edit(embed=embed, view=view)

    async def staff_list_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Staff List Configuration",
            description="Add roles to be displayed in the staff list. They will be displayed in the order of the position of the role.",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        staff_list_roles = doc["staff_list_roles"]
        original_interaction = interaction
        if guild in staff_list_roles:
            embed.add_field(name="Roles", value=", ".join(f"<@&{role}>" for role in staff_list_roles[guild]), inline=True)
        else:
            embed.add_field(name="Roles", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            staff_list_roles = doc["staff_list_roles"]
            new_embed = nextcord.Embed(
                title="Staff List Configuration",
                description="Add roles to be displayed in the staff list. They will be displayed in the order of the position of the role.",
                color=nextcord.Color.blue()
            )
            if guild in staff_list_roles:
                new_embed.add_field(name="Roles", value=", ".join(f"<@&{role}>" for role in staff_list_roles[guild]), inline=True)
            else:
                new_embed.add_field(name="Roles", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def add_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                current = configuration.find_one({"_id": "config"})["staff_list_roles"]
                if guild in current:
                    current = current[guild]
                else:
                    current = []
                for role in role_select.values:
                    if role.id in current:
                        current.remove(role.id)
                    else:
                        current.append(role.id)
                configuration.update_one({"_id": "config"}, {"$set": {f"staff_list_roles.{guild}": current}})
                await update_config_embed(original_interaction)

            role_select = nextcord.ui.RoleSelect(placeholder="Select a role to add/remove", max_values=25)
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_staff_list(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"staff_list_roles.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Staff list module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Add/Remove Roles", style=nextcord.ButtonStyle.primary, emoji="🪄")
        button.callback = add_role
        view.add_item(button)
        disable_button = nextcord.ui.Button(label="Disable Module", style=nextcord.ButtonStyle.danger, emoji="❌")
        disable_button.callback = disable_staff_list
        view.add_item(disable_button)
        await interaction.message.edit(embed=embed, view=view)

    async def strike_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Strike Configuration",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        strike_log = doc["strike_log"]
        strike_announce = doc["strike_announce"]
        original_interaction = interaction
        if guild in strike_log:
            embed.add_field(name="Strike Log Channel", value=f"{DOT} <#{strike_log[guild]}>", inline=True)
        else:
            embed.add_field(name="Strike Log Channel", value="None", inline=True)
        
        if guild in strike_announce:
            embed.add_field(name="Strike Announce Channel", value=f"{DOT} <#{strike_announce[guild]}>", inline=True)
        else:
            embed.add_field(name="Strike Announce Channel", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            strike_log = doc["strike_log"]
            strike_announce = doc["strike_announce"]
            new_embed = nextcord.Embed(
                title="Strike Configuration",
                color=nextcord.Color.blue()
            )
            if guild in strike_log:
                new_embed.add_field(name="Strike Log Channel", value=f"{DOT} <#{strike_log[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Strike Log Channel", value="None", inline=True)
            if guild in strike_announce:
                new_embed.add_field(name="Strike Announce Channel", value=f"{DOT} <#{strike_announce[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Strike Announce Channel", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_strike_log_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Strike Log Channel",
                max_values=1
            )
            old_interaction = interaction

            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"strike_log.{guild}": channel}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_strike_announce_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Strike Announce Channel",
                max_values=1
            )
            old_interaction = interaction

            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"strike_announce.{guild}": channel}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_strike_system(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            configuration.update_one({"_id": "config"}, {"$unset": {f"strike_log.{guild}": ""}})
            configuration.update_one({"_id": "config"}, {"$unset": {f"strike_announce.{guild}": ""}})
            await update_config_embed(original_interaction)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Strike Log Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button.callback = set_strike_log_channel
        view.add_item(button)
        button3 = nextcord.ui.Button(label="Set Strike Announce Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button3.callback = set_strike_announce_channel
        view.add_item(button3)
        button2 = nextcord.ui.Button(label="Disable Strike System", style=nextcord.ButtonStyle.danger, emoji="❌")
        button2.callback = disable_strike_system
        view.add_item(button2)
        await interaction.message.edit(embed=embed, view=view)

    async def counting_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Counting Configuration",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        counting_channel = doc["counting"]
        original_interaction = interaction
        if guild in counting_channel:
            embed.add_field(name="Counting Channel", value=f"{DOT} <#{counting_channel[guild]}>", inline=True)
        else:
            embed.add_field(name="Counting Channel", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            counting_channel = doc["counting"]
            new_embed = nextcord.Embed(
                title="Counting Configuration",
                color=nextcord.Color.blue()
            )
            if guild in counting_channel:
                new_embed.add_field(name="Counting Channel", value=f"{DOT} <#{counting_channel[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Counting Channel", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_counting_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Counting Channel",
                max_values=1
            )
            old_interaction = interaction
            
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"counting.{guild}": channel}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_counting(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            configuration.update_one({"_id": "config"}, {"$unset": {f"counting.{guild}": ""}})
            await update_config_embed(original_interaction)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Counting Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button.callback = set_counting_channel
        view.add_item(button)
        button2 = nextcord.ui.Button(label="Disable Counting", style=nextcord.ButtonStyle.danger, emoji="❌")
        button2.callback = disable_counting
        view.add_item(button2)
        await interaction.message.edit(embed=embed, view=view)

    async def utility_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Utility Configuration",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        original_interaction = interaction
        doc = configuration.find_one({"_id": "config"})
        poll_role = doc["poll_role"]
        lock_role = doc["lock_role"]
        player_role = doc["player_role"]
        event_manager_role = doc["event_manager_role"]
        role_cmd_access_roles = doc["role_cmd_access_roles"]
        if guild in poll_role:
            embed.add_field(name="Poll Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in poll_role[guild]])}", inline=False)
        else:
            embed.add_field(name="Poll Roles", value="None", inline=False)
        if guild in lock_role:
            embed.add_field(name="Lock Access Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in lock_role[guild]])}", inline=False)
        else:
            embed.add_field(name="Lock Access Roles", value="None", inline=False)
        if guild in player_role:
            embed.add_field(name="Player Role", value=f"{DOT} <@&{player_role[guild]}>", inline=True)
        else:
            embed.add_field(name="Player Role", value="None", inline=False)
        if guild in event_manager_role:
            embed.add_field(name="Event Manager Role", value=f"{DOT} <@&{event_manager_role[guild]}>", inline=True)
        else:
            embed.add_field(name="Event Manager Role", value="None", inline=True)
        if guild in role_cmd_access_roles:
            embed.add_field(name="Role Command Access Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in role_cmd_access_roles[guild]])}", inline=False)
        else:
            embed.add_field(name="Role Command Access Roles", value="None", inline=False)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            poll_role = doc["poll_role"]
            lock_role = doc["lock_role"]
            player_role = doc["player_role"]
            event_manager_role = doc["event_manager_role"]
            role_cmd_access_roles = doc["role_cmd_access_roles"]
            new_embed = nextcord.Embed(
                title="Utility Configuration",
                color=nextcord.Color.blue()
            )
            if guild in poll_role:
                new_embed.add_field(name="Poll Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in poll_role[guild]])}", inline=False)
            else:
                new_embed.add_field(name="Poll Roles", value="None", inline=False)
            if guild in lock_role:
                new_embed.add_field(name="Lock Access Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in lock_role[guild]])}", inline=False)
            else:
                new_embed.add_field(name="Lock Access Roles", value="None", inline=False)
            if guild in player_role:
                new_embed.add_field(name="Player Role", value=f"{DOT} <@&{player_role[guild]}>", inline=False)
            else:
                new_embed.add_field(name="Player Role", value="None", inline=False)
            if guild in event_manager_role:
                new_embed.add_field(name="Event Manager Role", value=f"{DOT} <@&{event_manager_role[guild]}>", inline=False)
            else:
                new_embed.add_field(name="Event Manager Role", value="None", inline=False)
            if guild in role_cmd_access_roles:
                new_embed.add_field(name="Role Command Access Roles", value=f"{DOT} {', '.join([f'<@&{role_id}>' for role_id in role_cmd_access_roles[guild]])}", inline=False)
            else:
                new_embed.add_field(name="Role Command Access Roles", value="None", inline=False)
            await interaction.message.edit(embed=new_embed)

        async def set_poll_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Poll Roles",
                max_values=25
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                role_ids = [role.id for role in roles]
                
                doc = configuration.find_one({"_id": "config"})
                poll_role = doc.get("poll_role", {})
                current_roles = poll_role.get(guild, [])
                
                updated_roles = []
                for role_id in role_ids:
                    if role_id not in current_roles:
                        updated_roles.append(role_id)
                    
                for role_id in current_roles:
                    if role_id not in role_ids:
                        updated_roles.append(role_id)
                        
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"poll_role.{guild}": updated_roles}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content="Poll roles updated", ephemeral=True)
            
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_lock_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Lock Access Roles",
                max_values=25
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                role_ids = [role.id for role in roles]
                
                doc = configuration.find_one({"_id": "config"})
                lock_role = doc.get("lock_role", {})
                current_roles = lock_role.get(guild, [])
                
                updated_roles = []
                for role_id in role_ids:
                    if role_id not in current_roles:
                        updated_roles.append(role_id)
                    
                for role_id in current_roles:
                    if role_id not in role_ids:
                        updated_roles.append(role_id)
                        
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"lock_role.{guild}": updated_roles}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content="Lock access roles updated", ephemeral=True)
            
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_player_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Player Role",
                max_values=1
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"player_role.{guild}": role.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content="Player role updated", ephemeral=True)
            
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_event_manager_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Event Manager Role",
                max_values=1
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"event_manager_role.{guild}": role.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content="Event manager role updated", ephemeral=True)
            
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_role_cmd_access_roles(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Role Command Access Roles",
                max_values=25
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                role_ids = [role.id for role in roles]
                
                doc = configuration.find_one({"_id": "config"})
                role_cmd_access = doc.get("role_cmd_access_roles", {})
                current_roles = role_cmd_access.get(guild, [])
                
                updated_roles = []
                for role_id in role_ids:
                    if role_id not in current_roles:
                        updated_roles.append(role_id)
                    
                for role_id in current_roles:
                    if role_id not in role_ids:
                        updated_roles.append(role_id)
                        
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"role_cmd_access_roles.{guild}": updated_roles}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content="Role command access roles updated", ephemeral=True)
            
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_utility(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"poll_role.{guild}": "", f"lock_role.{guild}": "", f"player_role.{guild}": "", f"event_manager_role.{guild}": "", f"role_cmd_access_roles.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Utility module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Poll Roles", style=nextcord.ButtonStyle.primary, emoji="📊")
        button.callback = set_poll_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Set Lock Access Roles", style=nextcord.ButtonStyle.primary, emoji="🔒")
        button.callback = set_lock_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Set Player Role", style=nextcord.ButtonStyle.primary, emoji="🎮")
        button.callback = set_player_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Set Event Manager Role", style=nextcord.ButtonStyle.primary, emoji="📅")
        button.callback = set_event_manager_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Set Role Cmd Access Roles", style=nextcord.ButtonStyle.primary, emoji="🔑")
        button.callback = set_role_cmd_access_roles
        view.add_item(button)
        button = nextcord.ui.Button(label="Disable Utility", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_utility
        view.add_item(button)
        await interaction.message.edit(embed=embed, view=view)

    async def mafia_logs_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Mafia Logs Configuration",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        original_interaction = interaction
        mafia_logs = doc["mafia_logs"]
        if guild in mafia_logs:
            embed.add_field(name="Mafia Logs Channel", value=f"{DOT} <#{mafia_logs[guild]}>", inline=True)
        else:
            embed.add_field(name="Mafia Logs Channel", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            mafia_logs = doc["mafia_logs"]
            new_embed = nextcord.Embed(
                title="Mafia Logs Configuration",
                color=nextcord.Color.blue()
            )
            if guild in mafia_logs:
                new_embed.add_field(name="Mafia Logs Channel", value=f"{DOT} <#{mafia_logs[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Mafia Logs Channel", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_mafia_logs_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Mafia Logs Channel",
                max_values=1
            )
            old_interaction = interaction

            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"mafia_logs.{guild}": channel}})
                await update_config_embed(old_interaction)
            
            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_mafia_logs(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            configuration.update_one({"_id": "config"}, {"$unset": {f"mafia_logs.{guild}": ""}})
            await update_config_embed(original_interaction)


        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Mafia Logs Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button.callback = set_mafia_logs_channel
        view.add_item(button)
        button = nextcord.ui.Button(label="Disable Mafia Logs", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_mafia_logs
        view.add_item(button)
        await interaction.message.edit(embed=embed, view=view)

    async def suggestions_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Suggestions Configuration",
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        suggestions = doc["suggestions"]
        suggestion_role = doc["suggestion_role"]
        no_suggestions = doc["no_suggestions"]
        original_interaction = interaction
        if guild in suggestions:
            embed.add_field(name="Suggestions Channel", value=f"{DOT} <#{suggestions[guild]}>", inline=True)
        else:
            embed.add_field(name="Suggestions Channel", value="None", inline=True)
        if guild in suggestion_role:
            embed.add_field(name="Suggestion Role", value=f"{DOT} <@&{suggestion_role[guild]}>", inline=True)
        else:
            embed.add_field(name="Suggestion Role", value="None", inline=True)
        if guild in no_suggestions:
            embed.add_field(name="No Suggestions Role", value=f"{DOT} <@&{no_suggestions[guild]}>", inline=True)
        else:
            embed.add_field(name="No Suggestions Role", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            suggestions = doc["suggestions"]
            suggestion_role = doc["suggestion_role"]
            no_suggestions = doc["no_suggestions"]
            new_embed = nextcord.Embed(
                title="Suggestions Configuration",
                color=nextcord.Color.blue()
            )

            if guild in suggestions:
                new_embed.add_field(name="Suggestions Channel", value=f"{DOT} <#{suggestions[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Suggestions Channel", value="None", inline=True)
            if guild in suggestion_role:
                new_embed.add_field(name="Suggestion Role", value=f"{DOT} <@&{suggestion_role[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Suggestion Role", value="None", inline=True)
            if guild in no_suggestions:
                new_embed.add_field(name="No Suggestions Role", value=f"{DOT} <@&{no_suggestions[guild]}>", inline=True)
            else:
                new_embed.add_field(name="No Suggestions Role", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_suggestions_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Suggestions Channel",
                max_values=1
            )
            old_interaction = interaction

            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"suggestions.{guild}": channel}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_suggestion_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Suggestion Role",
                max_values=1
            )
            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values
                role = role[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"suggestion_role.{guild}": role}})
                await update_config_embed(old_interaction)

            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def set_no_suggestions_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select No Suggestions Role",
                max_values=1
            )

            old_interaction = interaction

            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values
                role = role[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"no_suggestions.{guild}": role}})
                await update_config_embed(old_interaction)

            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.send(view=view, ephemeral=True)

        async def disable_suggestions(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"suggestions.{guild}": "", f"suggestion_role.{guild}": "", f"no_suggestions.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Suggestions module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Suggestions Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button.callback = set_suggestions_channel
        view.add_item(button)
        button = nextcord.ui.Button(label="Set Suggestion Role", style=nextcord.ButtonStyle.primary, emoji="🎗️")
        button.callback = set_suggestion_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Set No Suggestions Role", style=nextcord.ButtonStyle.primary, emoji="❌")
        button.callback = set_no_suggestions_role
        view.add_item(button)
        button = nextcord.ui.Button(label="Disable Suggestions", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_suggestions
        view.add_item(button)
        await interaction.message.edit(embed=embed, view=view)

    async def credits_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Credit System Configuration",
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        doc = credit_config.find_one({"_id": "config"})
        if guild in doc:
            embed.add_field(name="Credits", value=f"{DOT} {credits[guild]}", inline=True)
        else:
            embed.add_field(name="Credits", value="None", inline=True)

    async def auction_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Auction Configuration",
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        original_interaction = interaction
        doc = configuration.find_one({"_id": "config"})
        auction = doc["auction"]
        lock_on_end = doc["auction_lock_on_end"]
        auction_role = doc["auction_role"]
        auction_manager = doc["auction_manager"]
        if guild in auction:
            embed.add_field(name="Auction Channel", value=f"{DOT} <#{auction[guild]}>", inline=True)
        else:
            embed.add_field(name="Auction Channel", value="None", inline=True)
        
        if guild in lock_on_end:
            embed.add_field(name="Lock on End", value="Enabled", inline=True)
        else:
            embed.add_field(name="Lock on End", value="Disabled", inline=True)

        if guild in auction_role:
            embed.add_field(name="Auction End Role", value=f"{DOT} <@&{auction_role[guild]}>", inline=True)
        else:
            embed.add_field(name="Auction End Role", value="None", inline=True)

        if guild in auction_manager:
            roles = ", ".join([f"<@&{role_id}>" for role_id in auction_manager[guild]])
            embed.add_field(name="Auction Managers", value=f"{DOT} {roles}", inline=False)
        else:
            embed.add_field(name="Auction Managers", value="None", inline=False)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            auction = doc["auction"]
            lock_on_end = doc["auction_lock_on_end"]
            auction_role = doc["auction_role"]
            auction_manager = doc["auction_manager"]
            new_embed = nextcord.Embed(
                title="Auction Configuration",
                color=nextcord.Color.blue()
            )
            if guild in auction:
                new_embed.add_field(name="Auction Channel", value=f"{DOT} <#{auction[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Auction Channel", value="None", inline=True)
            if guild in lock_on_end:
                new_embed.add_field(name="Lock on End", value="Enabled", inline=True)
            else:
                new_embed.add_field(name="Lock on End", value="Disabled", inline=True)
            if guild in auction_role:
                new_embed.add_field(name="Auction End Role", value=f"{DOT} <@&{auction_role[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Auction End Role", value="None", inline=True)
            if guild in auction_manager:
                roles = ", ".join([f"<@&{role_id}>" for role_id in auction_manager[guild]])
                new_embed.add_field(name="Auction Managers", value=f"{DOT} {roles}", inline=False)
            else:
                new_embed.add_field(name="Auction Managers", value="None", inline=False)
            await interaction.message.edit(embed=new_embed)

        async def set_auction_channel(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Auction Channel",
                max_values=1
            )
            
            old_interaction = interaction
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values
                channel = channel[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"auction.{guild}": channel}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_lock_on_end(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            doc = configuration.find_one({"_id": "config"})
            lock_on_end = doc["auction_lock_on_end"]
            if guild in lock_on_end:
                current_bool = lock_on_end[guild]
                if current_bool:
                    new_bool = False
                else:
                    new_bool = True 
            else:
                new_bool = True
            configuration.update_one({"_id": "config"}, {"$set": {f"auction_lock_on_end.{guild}": new_bool}})
            await update_config_embed(interaction)

        async def set_auction_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select Auction End Role",
                max_values=1
            )
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values
                role = role[0].id
                configuration.update_one({"_id": "config"}, {"$set": {f"auction_role.{guild}": role}})
                await update_config_embed(old_interaction)

            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_auction_manager(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Add/remove auction managers",
                max_values=25
            )

            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                current_doc = configuration.find_one({"_id": "config"})
                auction_manager = current_doc["auction_manager"]
                current_roles = []
                if guild in auction_manager:
                    current_roles = auction_manager[guild]
                
                for role in roles:
                    if role.id in current_roles:
                        current_roles.remove(role.id)
                    else:
                        current_roles.append(role.id)
                configuration.update_one({"_id": "config"}, {"$set": {f"auction_manager.{guild}": current_roles}})
                await update_config_embed(old_interaction)

            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def disable_auction(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"auction.{guild}": "", f"auction_lock_on_end.{guild}": "", f"auction_role.{guild}": "", f"auction_manager.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Auction module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Auction Channel", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button.callback = set_auction_channel
        view.add_item(button)
        lock_button = nextcord.ui.Button(label="Lock on End", style=nextcord.ButtonStyle.primary, emoji="🔒")
        lock_button.callback = set_lock_on_end
        view.add_item(lock_button)
        role_button = nextcord.ui.Button(label="Set Auction End Role", style=nextcord.ButtonStyle.primary, emoji="🏆")
        role_button.callback = set_auction_role
        view.add_item(role_button)
        manager_button = nextcord.ui.Button(label="Set Auction Managers", style=nextcord.ButtonStyle.primary, emoji="👑")
        manager_button.callback = set_auction_manager
        view.add_item(manager_button)
        button = nextcord.ui.Button(label="Disable Auction", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_auction
        view.add_item(button)
        await interaction.message.edit(embed=embed, view=view)

    async def auto_lock(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Auto-Lock Configuration",
            description="This module automatically locks/unlocks the channel if a rumble starts/ends.",
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        original_interaction = interaction
        doc = configuration.find_one({"_id": "config"})
        auto_lock = doc["auto_lock"]
        if guild in auto_lock:
            if auto_lock[guild]["status"]:
                embed.add_field(name="Auto-Unlock/Lock", value="Enabled", inline=True)
                channels = ", ".join([f"<#{channel}>" for channel in auto_lock[guild]["channels"]])
                if channels == "":
                    channels = "None"
                embed.add_field(name="Valid Channels", value=f"{channels}", inline=True)
            else:
                channels = ", ".join([f"<#{channel}>" for channel in auto_lock[guild]["channels"]])
                embed.add_field(name="Auto-Unlock/Lock", value="Disabled", inline=True)
                if channels == "":
                    channels = "None"
                embed.add_field(name="Valid Channels", value=f"{channels}", inline=True)
        else:
            embed.add_field(name="Auto-Unlock/Lock", value="Disabled", inline=True)
            embed.add_field(name="Valid Channels", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            auto_lock = doc["auto_lock"]
            new_embed = nextcord.Embed(
                title="Auto-Lock Configuration",
                color=nextcord.Color.blue(),
                description="This module automatically locks/unlocks the channel if a rumble starts/ends."
            )
            if guild in auto_lock:
                if auto_lock[guild]["status"]:
                    new_embed.add_field(name="Auto-Unlock/Lock", value="Enabled", inline=True)
                    channels = ", ".join([f"<#{channel}>" for channel in auto_lock[guild]["channels"]])
                    if channels == "":
                        channels = "None"
                    new_embed.add_field(name="Valid Channels", value=f"{channels}", inline=True)
                else:
                    new_embed.add_field(name="Auto-Unlock/Lock", value="Disabled", inline=True)
                    channels = ", ".join([f"<#{channel}>" for channel in auto_lock[guild]["channels"]])
                    if channels == "":
                        channels = "None"
                    new_embed.add_field(name="Valid Channels", value=f"{channels}", inline=True)
            else:
                new_embed.add_field(name="Auto-Unlock/Lock", value="Disabled", inline=True)
                new_embed.add_field(name="Valid Channels", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_auto_lock(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            doc = configuration.find_one({"_id": "config"})
            auto_lock = doc["auto_lock"]
            if guild in auto_lock:
                existing_channels = auto_lock[guild].get("channels", [])
                if auto_lock[guild]["status"]:
                    configuration.update_one({"_id": "config"}, {"$set": {f"auto_lock.{guild}": {"status": False, "channels": existing_channels}}})
                else:
                    configuration.update_one({"_id": "config"}, {"$set": {f"auto_lock.{guild}": {"status": True, "channels": existing_channels}}})
            else:
                configuration.update_one({"_id": "config"}, {"$set": {f"auto_lock.{guild}": {"status": True, "channels": []}}})
            await update_config_embed(interaction)

        async def set_auto_lock_channels(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select Channels",
                max_values=25
            )

            old_interaction = interaction
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channels = channel_select.values
                current_doc = configuration.find_one({"_id": "config"})
                auto_lock = current_doc["auto_lock"]
                current_channels = auto_lock.get(guild, {}).get("channels", [])
                existing_status = auto_lock.get(guild, {}).get("status", False)
                new_channels = []
                for channel in channels:
                    if channel.id not in current_channels:
                        new_channels.append(channel.id)
                    else:
                        current_channels.remove(channel.id)
                configuration.update_one({"_id": "config"}, {"$set": {f"auto_lock.{guild}": {"status": existing_status, "channels": new_channels + current_channels}}})
                await update_config_embed(old_interaction)

            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.send(view=view, ephemeral=True)

        button = nextcord.ui.Button(label="Enable/Disable", style=nextcord.ButtonStyle.primary, emoji="🛑")
        button.callback = set_auto_lock
        view = View(self.bot)
        view.add_item(button)
        button2 = nextcord.ui.Button(label="Set Channels", style=nextcord.ButtonStyle.primary, emoji="#️⃣")
        button2.callback = set_auto_lock_channels
        view.add_item(button2)
        await interaction.message.edit(embed=embed, view=view)
            
    async def highlight_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Highlight Configuration",
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        original_interaction = interaction
        doc = configuration.find_one({"_id": "config"})
        highlight = doc["highlight"]
        if guild in highlight:
            roles = [f"<@&{role_id}>" for role_id in highlight[guild]]
            roles = ", ".join(roles)
            embed.add_field(name="Access Roles", value=f"{DOT} {roles}", inline=True)
        else:
            embed.add_field(name="Access Roles", value="None", inline=True)

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            highlight = doc["highlight"]
            new_embed = nextcord.Embed(
                title="Highlight Configuration",
                color=nextcord.Color.blue()
            )
            if guild in highlight:
                roles = [f"<@&{role_id}>" for role_id in highlight[guild]]
                roles = ", ".join(roles)
                new_embed.add_field(name="Access Roles", value=f"{DOT} {roles}", inline=True)
            else:
                new_embed.add_field(name="Access Roles", value="None", inline=True)
            await interaction.message.edit(embed=new_embed)

        async def set_access_roles(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Add/remove access roles",
                max_values=25
            )
            
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                current_doc = configuration.find_one({"_id": "config"})
                highlight = current_doc["highlight"]
                current_roles = []
                if guild in highlight:
                    current_roles = highlight[guild]
                for role in roles:
                    if role.id in current_roles:
                        current_roles.remove(role.id)
                    else:
                        current_roles.append(role.id)
                configuration.update_one({"_id": "config"}, {"$set": {f"highlight.{guild}": current_roles}})
                await update_config_embed(old_interaction)

            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def disable_highlight(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"highlight.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Highlight module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        button = nextcord.ui.Button(label="Set Access Roles", style=nextcord.ButtonStyle.primary, emoji="🔒")
        button.callback = set_access_roles
        view.add_item(button)
        button = nextcord.ui.Button(label="Disable Highlight", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_highlight
        view.add_item(button)
        await interaction.message.edit(embed=embed, view=view)

    async def ar_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Auto-Responder Configuration", 
            color=nextcord.Color.blue()
        )

        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "ar_config"})
        link_allowed = doc["link_allowed"]
        words_allowed = doc["words_allowed"]
        allowed = doc["allowed"]

        if guild in link_allowed:
            roles = [f"<@&{role_id}>" for role_id in link_allowed[guild]]
            embed.add_field(name="Link Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=True)
        else:
            embed.add_field(name="Link Allowed Roles", value="None", inline=True)
        if guild in words_allowed:
            roles = [f"<@&{role_id}>" for role_id in words_allowed[guild]]
            embed.add_field(name="Words Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=True)
        else:
            embed.add_field(name="Words Allowed Roles", value="None", inline=True)
        if guild in allowed:
            roles = [f"<@&{role_id}>" for role_id in allowed[guild]]
            embed.add_field(name="AR Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=False)
        else:
            embed.add_field(name="AR Allowed Roles", value="None", inline=False)

        original_interaction = interaction

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "ar_config"})
            link_allowed = doc["link_allowed"]
            words_allowed = doc["words_allowed"]
            allowed = doc["allowed"]
            
            new_embed = nextcord.Embed(
                title="Auto-Responder Configuration",
                color=nextcord.Color.blue()
            )
            
            if guild in link_allowed:
                roles = [f"<@&{role_id}>" for role_id in link_allowed[guild]]
                new_embed.add_field(name="Link Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=True)
            else:
                new_embed.add_field(name="Link Allowed Roles", value="None", inline=True)
            if guild in words_allowed:
                roles = [f"<@&{role_id}>" for role_id in words_allowed[guild]]
                new_embed.add_field(name="Words Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=True)
            else:
                new_embed.add_field(name="Words Allowed Roles", value="None", inline=True)
            if guild in allowed:
                roles = [f"<@&{role_id}>" for role_id in allowed[guild]]
                new_embed.add_field(name="AR Allowed Roles", value=f"{DOT} " + f"{DOT} ".join(roles), inline=False)
            else:
                new_embed.add_field(name="AR Allowed Roles", value="None", inline=False)

            await interaction.message.edit(embed=new_embed)

        async def set_link_allowed(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Add/remove link allowed roles",
                max_values=25
            )
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                current_doc = configuration.find_one({"_id": "ar_config"})
                link_allowed = current_doc["link_allowed"]
                current_roles = []
                if guild in link_allowed:
                    current_roles = link_allowed[guild]
                for role in roles:
                    if role.id in current_roles:
                        current_roles.remove(role.id)
                    else:
                        current_roles.append(role.id)
                configuration.update_one({"_id": "ar_config"}, {"$set": {f"link_allowed.{guild}": current_roles}})
                await update_config_embed(old_interaction)
                
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_words_allowed(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Add/remove words allowed roles",
                max_values=25
            )
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                current_doc = configuration.find_one({"_id": "ar_config"})
                words_allowed = current_doc["words_allowed"]
                current_roles = []
                if guild in words_allowed:
                    current_roles = words_allowed[guild]
                for role in roles:
                    if role.id in current_roles:
                        current_roles.remove(role.id)
                    else:
                        current_roles.append(role.id)
                configuration.update_one({"_id": "ar_config"}, {"$set": {f"words_allowed.{guild}": current_roles}})
                await update_config_embed(old_interaction)
                
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_allowed(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Add/remove AR allowed roles",
                max_values=25
            )
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                roles = role_select.values
                current_doc = configuration.find_one({"_id": "ar_config"})
                allowed = current_doc["allowed"]
                current_roles = []
                if guild in allowed:
                    current_roles = allowed[guild]
                for role in roles:
                    if role.id in current_roles:
                        current_roles.remove(role.id)
                    else:
                        current_roles.append(role.id)
                configuration.update_one({"_id": "ar_config"}, {"$set": {f"allowed.{guild}": current_roles}})
                await update_config_embed(old_interaction)
                
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def disable_ar(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "ar_config"}, {"$unset": {f"link_allowed.{guild}": "", f"words_allowed.{guild}": "", "allowed.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Auto-Responder module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        
        link_allowed_button = nextcord.ui.Button(label="Set Link Allowed Roles", style=nextcord.ButtonStyle.primary, custom_id="set_link_allowed", emoji="🔗")
        words_allowed_button = nextcord.ui.Button(label="Set Words Allowed Roles", style=nextcord.ButtonStyle.primary, custom_id="set_words_allowed", emoji="📝") 
        allowed_button = nextcord.ui.Button(label="Set AR Allowed Roles", style=nextcord.ButtonStyle.primary, custom_id="set_allowed", emoji="💬")

        link_allowed_button.callback = set_link_allowed
        words_allowed_button.callback = set_words_allowed
        allowed_button.callback = set_allowed

        view.add_item(link_allowed_button)
        view.add_item(words_allowed_button)
        view.add_item(allowed_button)
        button = nextcord.ui.Button(label="Disable AR", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_ar
        view.add_item(button)

        await interaction.message.edit(embed=embed, view=view)
        
    
    async def payout_config(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Payout Configuration",
            color=nextcord.Color.blue()
        )
        guild = str(interaction.guild.id)
        doc = configuration.find_one({"_id": "config"})
        original_interaction = interaction
        payout = doc["payout"]
        claim = doc["claim"]
        queue = doc["queue"]
        root = doc["root"]
        if guild in payout:
            embed.add_field(name="Payout Channel", value=f"{DOT} <#{payout[guild]}>", inline=True)
        else:
            embed.add_field(name="Payout Channel", value="None", inline=True)
        if guild in claim:
            embed.add_field(name="Claim Channel", value=f"{DOT} <#{claim[guild]}>", inline=True)
        else:
            embed.add_field(name="Claim Channel", value="None", inline=True)
        if guild in queue:
            embed.add_field(name="Queue Channel", value=f"{DOT} <#{queue[guild]}>", inline=False)
        else:
            embed.add_field(name="Queue Channel", value="None", inline=False)
        if guild in root:
            embed.add_field(name="Payout Role", value=f"{DOT} <@&{root[guild]}>", inline=False)
        else:
            embed.add_field(name="Payout Role", value="None", inline=False)

        old_interaction = interaction

        async def update_config_embed(interaction: nextcord.Interaction):
            doc = configuration.find_one({"_id": "config"})
            payout = doc["payout"]
            claim = doc["claim"]
            queue = doc["queue"]
            root = doc["root"]
            
            new_embed = nextcord.Embed(
                title="Payout Configuration",
                color=nextcord.Color.blue()
            )
            
            if guild in payout:
                new_embed.add_field(name="Payout Channel", value=f"{DOT} <#{payout[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Payout Channel", value="None", inline=True)
            if guild in claim:
                new_embed.add_field(name="Claim Channel", value=f"{DOT} <#{claim[guild]}>", inline=True)
            else:
                new_embed.add_field(name="Claim Channel", value="None", inline=True)
            if guild in queue:
                new_embed.add_field(name="Queue Channel", value=f"{DOT} <#{queue[guild]}>", inline=False)
            else:
                new_embed.add_field(name="Queue Channel", value="None", inline=False)
            if guild in root:
                new_embed.add_field(name="Payout Role", value=f"{DOT} <@&{root[guild]}>", inline=False)
            else:
                new_embed.add_field(name="Payout Role", value="None", inline=False)
                
            await old_interaction.message.edit(embed=new_embed)

        async def set_payout(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select payout channel,",
                channel_types=[nextcord.ChannelType.text]
            )
            old_interaction = interaction
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"payout.{guild}": channel.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content=f"Payout channel set to {channel.mention}", ephemeral=True)
                
            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_claim(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select claim channel",
                channel_types=[nextcord.ChannelType.text]
            )
            old_interaction = interaction
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"claim.{guild}": channel.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content=f"Claim channel set to {channel.mention}", ephemeral=True)
                
            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_queue(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            channel_select = nextcord.ui.ChannelSelect(
                placeholder="Select queue channel",
                channel_types=[nextcord.ChannelType.text]
            )
            old_interaction = interaction
            async def channel_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                channel = channel_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"queue.{guild}": channel.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content=f"Queue channel set to {channel.mention}", ephemeral=True)
                
            channel_select.callback = channel_callback
            view = nextcord.ui.View()
            view.add_item(channel_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def set_role(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            role_select = nextcord.ui.RoleSelect(
                placeholder="Select payout role"
            )
            old_interaction = interaction
            async def role_callback(interaction: nextcord.Interaction):
                await interaction.response.defer(ephemeral=True)
                role = role_select.values[0]
                configuration.update_one(
                    {"_id": "config"},
                    {"$set": {f"root.{guild}": role.id}}
                )
                await update_config_embed(old_interaction)
                await interaction.send(content=f"Payout role set to {role.mention}", ephemeral=True)
                
            role_select.callback = role_callback
            view = nextcord.ui.View()
            view.add_item(role_select)
            await interaction.response.send_message(view=view, ephemeral=True)

        async def disable_payout(interaction: nextcord.Interaction):
            if interaction.user.id != original_interaction.user.id:
                await interaction.response.send_message("You are not the original user who initiated the command.", ephemeral=True)
                return
            await interaction.response.defer(ephemeral=True)
            
            configuration.update_one({"_id": "config"}, {"$unset": {f"payout.{guild}": "", f"claim.{guild}": "", f"queue.{guild}": "", f"root.{guild}": ""}})
            
            await update_config_embed(original_interaction)
            await interaction.followup.send("Payout module disabled for this server.", ephemeral=True)

        view = View(self.bot)
        
        payout_button = nextcord.ui.Button(label="Set Payout Channel", style=nextcord.ButtonStyle.primary, custom_id="set_payout", emoji=CHANNEL)
        claim_button = nextcord.ui.Button(label="Set Claim Channel", style=nextcord.ButtonStyle.primary, custom_id="set_claim", emoji=CHANNEL)
        queue_button = nextcord.ui.Button(label="Set Queue Channel", style=nextcord.ButtonStyle.primary, custom_id="set_queue", emoji=CHANNEL)
        role_button = nextcord.ui.Button(label="Set Payout Role", style=nextcord.ButtonStyle.primary, custom_id="set_role", emoji="💵")
        button = nextcord.ui.Button(label="Disable Payout", style=nextcord.ButtonStyle.danger, emoji="❌")
        button.callback = disable_payout
        view.add_item(button)
        
        payout_button.callback = set_payout
        claim_button.callback = set_claim
        queue_button.callback = set_queue
        role_button.callback = set_role

        view.add_item(payout_button)
        view.add_item(claim_button)
        view.add_item(queue_button)
        view.add_item(role_button)

        await interaction.message.edit(embed=embed, view=view)

def setup(bot):
    bot.add_cog(Config(bot))
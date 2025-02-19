import nextcord
from nextcord.ext import commands

class HomeView(nextcord.ui.View):
    def __init__(self):
        super().__init__()
        home_button = nextcord.ui.Button(label="Home", emoji="🏠")
        home_button.callback = self.home_button_callback
        self.add_item(home_button)

    async def home_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Compass Bot Help",
            description="This is the help page for Compass Bot. If you need additional help, please join the support server: https://discord.gg/WjKxvG58JJ. Use the buttons below to navigate to the different categories.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=View())

class View(nextcord.ui.View):
    def __init__(self):
        super().__init__()

        admin_button = nextcord.ui.Button(label="Admin", emoji="🔨")
        admin_button.callback = self.admin_button_callback
        self.add_item(admin_button)

        config_button = nextcord.ui.Button(label="Config", emoji="🔧")
        config_button.callback = self.config_button_callback
        self.add_item(config_button)

        auction_button = nextcord.ui.Button(label="Auction", emoji="🏆")
        auction_button.callback = self.auction_button_callback
        self.add_item(auction_button)

        counting_button = nextcord.ui.Button(label="Counting", emoji="🔢")
        counting_button.callback = self.counting_button_callback
        self.add_item(counting_button)

        gtn_button = nextcord.ui.Button(label="GTN", emoji="🥇")
        gtn_button.callback = self.gtn_button_callback
        self.add_item(gtn_button)

        rollkill_button = nextcord.ui.Button(label="Rollkill", emoji="🎲")
        rollkill_button.callback = self.rollkill_button_callback
        self.add_item(rollkill_button)

        sos_button = nextcord.ui.Button(label="SOS", emoji="🚨")
        sos_button.callback = self.sos_button_callback
        self.add_item(sos_button)

        misc_button = nextcord.ui.Button(label="Misc", emoji="🛠️")
        misc_button.callback = self.misc_button_callback
        self.add_item(misc_button)

        payouts_button = nextcord.ui.Button(label="Payouts", emoji="💰")
        payouts_button.callback = self.payouts_button_callback
        self.add_item(payouts_button)

        auto_responder_button = nextcord.ui.Button(label="Auto Responder", emoji="🤖")
        auto_responder_button.callback = self.auto_responder_button_callback
        self.add_item(auto_responder_button)

        highlight_button = nextcord.ui.Button(label="Highlight", emoji="🔍")
        highlight_button.callback = self.highlight_button_callback
        self.add_item(highlight_button)

        pcms_button = nextcord.ui.Button(label="PCMS", emoji="#️⃣")
        pcms_button.callback = self.pcms_button_callback
        self.add_item(pcms_button)

        poll_button = nextcord.ui.Button(label="Poll", emoji="🗳️")
        poll_button.callback = self.poll_button_callback
        self.add_item(poll_button)

        role_and_utility_button = nextcord.ui.Button(label="Role and Utility", emoji="🎭")
        role_and_utility_button.callback = self.role_and_utility_button_callback
        self.add_item(role_and_utility_button)

        staff_button = nextcord.ui.Button(label="Staff", emoji="👨‍💼")
        staff_button.callback = self.staff_button_callback
        self.add_item(staff_button)

        suggestions_button = nextcord.ui.Button(label="Suggestions", emoji="💡")
        suggestions_button.callback = self.suggestions_button_callback
        self.add_item(suggestions_button)

    async def admin_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Admin Commands",
            description="Admin commands are commands that are only available to the server owner and bot admins.\n\n`!reload` - Reloads the bot cogs. \n`!load` - Loads a cog. \n`!unload` - Unloads a cog. \n`!botban` - Bans an user from using the bot.\n`!aping` - Detailed pinging stats.\n`!botadmin` - Adds or removes a user from the bot admin list. (owner only)",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def config_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Bot Configuration",
            description="By running `/config`, you can configure the bot to your liking. This will allow you to set up the payout system, the auction system, and more.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def auction_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Auction Commands",
            description="The Compass Auction system allows to auction off items to the highest bidder. This will allow you to start an auction, bid on an auction, and more. This needs to be configured in the `/config` command before you can use it. Once a channel is set, any donation will trigger an auction start. You can also reply to a message with `!auction` to start an auction. \n\n`!auction` - Starts an auction. \n`!auction set` - Allows configuring the auction settings like value, price, and more. \n`!auction end` - Ends an auction.\n\nAt the end, you can use the Queue Payouts button if the payouts system is configured.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def counting_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Counting",
            description="A channel needs to be set in `/config` command. Once that starts, you can start the counting. No counting twice in a row, or skipping numbers.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def gtn_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Guess the Number",
            description=f"Guess the number within the range. There is a 10% chance of the bot telling you if the number is higher or lower. \n\n`!gtn [highest num]` - Starts a guessing game. \n`!gtn end` - Ends a guessing game in that channel.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def rollkill_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def sos_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def misc_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def payouts_button_callback(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Payout System",
            description="The payouts system allows members to queue payouts for events and pay them out using a very fast process. This essentially makes payout much more simpler and easier for everyone. \n\n`/payout create` - Creates a payout queue.\n`/payout express` - Starts the payout process. \n`/payout multiple` - Allows you to queueu payouts for multiple users at once.\n`!pstats` - Shows the payout stats for the server.",
            color=nextcord.Color.blue()
        )
        await interaction.message.edit(embed=embed, view=HomeView())

    async def auto_responder_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def highlight_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def pcms_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def poll_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def role_and_utility_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def staff_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def suggestions_button_callback(self, interaction: nextcord.Interaction):
        pass

    async def other_button_callback(self, interaction: nextcord.Interaction):
        pass

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Help cog loaded")

    @commands.command(name="support")
    async def support_cmd(self, ctx):
        embed = nextcord.Embed(
            title="Support Server",
            description="If you need help, please join the support server: https://discord.gg/WjKxvG58JJ",
            color=nextcord.Color.blue()
        )
        await ctx.reply(embed=embed, mention_author=False)
    
    @commands.command(name="help")
    async def help_cmd(self, ctx):
        embed = nextcord.Embed(
            title="Compass Bot Help",
            description="This is the help page for Compass Bot. If you need additional help, please join the support server: https://discord.gg/WjKxvG58JJ. Use the buttons below to navigate to the different categories. This is still in development.",
            color=nextcord.Color.blue()
        )
        await ctx.reply(embed=embed, view=View(), mention_author=False)

    @nextcord.slash_command(name="help", description="Run this command to get help!")
    async def help_slash(self, interaction: nextcord.Interaction):
        embed = nextcord.Embed(
            title="Compass Bot Help",
            description="This is the help page for Compass Bot. If you need additional help, please join the support server: https://discord.gg/WjKxvG58JJ. Use the buttons below to navigate to the different categories. This is still in development.",
            color=nextcord.Color.blue()
        )
        await interaction.response.send_message(embed=embed,view=View())

def setup(bot):
    bot.add_cog(Help(bot))
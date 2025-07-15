import nextcord
from nextcord.ext import commands
from requests import post

class View(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

import nextcord

EVENT_GUIDE_MENUS = [
    {
        "label": "Tea Events",
        "description": "Guide for all the Mudae Tea Events",
        "value": "tea_events"
    },
    {
        "label": "Rumble Royale",
        "description": "Guide for Rumble Royale Events",
        "value": "rumble"
    },
    {
        "label": "Mafia",
        "description": "Guide for Mafia Games",
        "value": "mafia"
    },
    {
        "label": "Mafia Secret Gamemode",
        "description": "Guide for Mafia Secret Gamemode",
        "value": "mafia_secret"
    },
    {
        "label": "Gartic",
        "description": "Guide for Gartic Games",
        "value": "gartic"
    },
    {
        "label": "Guess the Item",
        "description": "Guide for Guess the Item Events",
        "value": "gti"
    },
    {
        "label": "Split or Steal",
        "description": "Guide for Split or Steal Events",
        "value": "split_or_steal"
    },
    {
        "label": "Simon Says Game",
        "description": "Guide for Simon Says Game Events",
        "value": "simon_says"
    },
    {
        "label": "Evolution of Trust",
        "description": "Guide for Evolution of Trust Events",
        "value": "eot"
    },
    {
        "label": "Wordle",
        "description": "Guide for Wordle Events",
        "value": "wordle"
    },
    {
        "label": "Rollkill",
        "description": "Guide for Rollkill Events",
        "value": "rollkill"
    },
    {
        "label": "Auction",
        "description": "Guide for Auction Events",
        "value": "auction"
    },
    {
        "label": "UNO",
        "description": "Guide for UNO Events",
        "value": "uno"
    },
    {
        "label": "Guess the Number",
        "description": "Guide for GTN Events",
        "value": "gtn"
    }
]

EVENT_GUIDE_EMBEDS = {
    "tea_events": {
        "title": "Tea Events",
        "description": """**Tea Events**

__1. Commands__
- Ping first, giving regular info about the event.
- Start a two minute timer then start the event after it ends. DO NOT ping again.
- Start tea using $[color]tea
- The color options are: Black, Green, Red, Yellow, Mixed
- Use -ul to unlock the channel before Mudae's countdown timer is complete

__2. Customization__
**Make sure to put the customization before the timer ends**
- $syll [number] to set the variety of words (higher = more and bigger and harder)
- $hp [number] to set lives in game that include lives
- $pts [number] to set the amount of points you need to win in games that include points
- $time to set the time limit of each “round”
- All of these have a default, and only use the commands if the donor asks. There is nothing you need to do to set it back to normal.
"""
    },
    "rumble": {
        "title": "Rumble Royale",
        "description": """**Rumble**

__1. Command__
- To start a rumble use the command /battle with <@693167035068317736>
- The time should always be 2 minutes if it’s below 100M value, if it’s above to 3 minutes.
- The type should always be normal unless you have a rumble room

__2. Customization__
- Donors are allowed to customize who gets the prize
- For example, first dead, whoever kills a specific person (bounty)
- The donor isn’t allowed to change their choice once the manager has pinged
- If the donor doesn’t specify, the prize goes to the winner

__3. Extra__
- Requirements are 100M+
- If the donor wins, give it to second place, unless it’s a bounty where you should then redo
- If the winner doesn’t do the requirement it is a redo
- Use event ping when pinging for a rumble
- Include the word rumble in your ping otherwise you will not receive credit

Run /chatrumble on <@1291996619490984037> if you would like to host a chat rumble.
"""
    },
    "mafia": {
        "title": "Mafia Games",
        "description": """__How to host__

- Host with <@758999095070687284>
- **Don't host any mafia with Classic gamemode unless the donor specifies, change it to random**
- Join the game using the command `/join`
- Make sure you are the only one in the party, if you're not, use `/clear` and rejoin the party again
- Use the `play-button` command, then send the ping message and set a 1 minute 30 second timer (90 seconds)
- Ping <@&1205270486263795712> only when hosting a mafia if the value is worth below 50m. Add <@&1205270486263795720> if the prize is worth 50m+
- Make sure to mention the prize of the mafia, the donor of the mafia (and to thank them in #chat), and any additional specs or requirement in the **same** message
- When the timer ends, press `Start game` (or use the `/setup` command). It will automatically setup and pull up rules
- Mention reading the rules if you want
- When the game finishes setting up there will be an embed that only you can see, press `Start` to start the game (or use the `/start` command).

__Notes__
- Don't unlock the channel when hosting, leave it locked and don't idle chat.
- If you are unable to finish the mafia game you started, ping a staff member to take over. Make sure they are available and promote them to host with the command `/new-leader`
- Do not promote someone who isn't an @event manager.
- If you want to host the game without playing you can press the `Leave` button once at least 1 more person has joined
- After the game ends queue payout for winners, make sure to not queue for donor
- Please don't double ping if you forget to ping <@&1205270486263795720>
"""
    },
    "mafia_secret": {
        "title": "Mafia Secret Gamemode",
        "description": """**Secret Gamemode**

Secret Gamemode can be turned on by going in `/settings`, clicking on `game modifiers` and toggling on the fifth option, `Secret Gamemode`.
Secret gamemode is a mode in mafia where a third team is introduced, the 4 horsemen (plague doctor, grave robber, farmer, and doomsayer) have to work together and be the last ones standing to win. The 4 roles can communicate with eachother via Mafia Bot dms and know their teammates, similar to how being mafia aligned works. 
- Secret Gamemode requires 19+ players 
- Secret Gamemode is strictly confined to the random gamemode. 
- Secret Gamemode cannot be guaranteed with custom rolelist 
- Secret Gamemode only occurs when all 4 horsemen appear in the same game
- Necronomicon Plague doctor must be toggled ON and other horsemen cannot be banned on `/custom rolelist ban`
"""
    },
    "gartic": {
        "title": "Gartic Games",
        "description": """**Gartic**

__1. How to start__
- Ping event ping with prize and donor etc
- Run g.gartic [category] to start (categories are: general [default], animals, verbs, movies, objects, cartoons, pokemon, foods, and flags)

__2. How to host__
- Donors are allowed to customize how many points to win (default 10)
- Let the gartic run until a person (not the donor) has reached that amount
- Run g.end to end the gartic
- During the game, if people are struggling to get the word, you may ask if they want a hint. If they say yes, run g.hint
- If it looks like the timer to answer is about to be up, run g.skip
- There are only 3 skips and 3 hints
- If the game ends before there is a winner, keep track of the original leaderboard and run the g.gartic command again, but keep track of the points from the previous leaderboard
"""
    },
    "gti": {
        "title": "Guess the Item",
        "description": """**GTI**

__How to host__
- If someone donates for gti, make sure to clarify what box they will be opening. If they don't have a box tell them they cannot do this event unless they have a box. They only dono the prize not the box.
- When they donate the prize and specify the box, go to your dm's with Dank Memer and do `/item: <whatever the box/bag name is>`
- Then, click the option that says `possible rewards` below the item. Screenshot the list of rewards inside the box. Copy and paste this screenshot into a event channel.
- Set the channel slowmode for 2m with the `/slowmode` command. Set a timer for 1 - 2min, depending on how many rewards are in the box.
- When the timer ends, add player `-p` to the person who donated for the event and tell them to open the box.
- Whoever guesses the item in the box first gets the prize.
- Queue the prize for the winner.

__Notes__
- If nobody guesses the item that the donor gets, it goes to the pool unless donor wants to redo with another event or another box.
- No editing guesses, if you see someone edit their guess it is invalid.
"""
    },
    "split_or_steal": {
        "title": "Split or Steal",
        "description": """**Split or Steal**

__1. Command__
- Use /sos on <@1291996619490984037> to start the game. Then do your normal ping.
- The players will automatically be chosen and given player.
- Ping the player[s] if they are afk.
- The players do not need to DM you as there is a button for them to click
- The player role is automatically removed at the end

__2. Winning__
- It’s very simple. If both people choose split, they split the prize
- If one steals and one splits the person who stole gets the whole prize
- Queue the prize
- If both people steal, neither person gets the prize and you redo. With another ping.
"""
    },
    "simon_says": {
        "title": "Simon Says Game",
        "description": """**Simon Says Game**

__How to host__
- Max amount of players = 10
- Like SOS, players will be selected randomly via a giveaway bot; I'd recommend giveaway boat as it auto gives them the player role
- Soon as the players are selected, do an activity check e.g. you could say "Simon says say hi" and have players respond with hi back. Any players who do not provide a response back within 30 seconds max will be eliminated
- Upon completion of the activity check, any players caught Idle chatting will result in an immediate elimination
- Editing or deleting messages will result in an event warn
- You can use prompts such as "Simon says say...", "Simon says tell me..", "Simon says solve...", "Simon Says answer" etc.
- You could also use prompts to trick the players e.g. "Simon say says...", "Simon says say tell me..." Simon says teII me..." etc.
- Players that respond incorrectly to the prompt or answer last will be eliminated; the last remaining player will win
"""
    },
    "eot": {
        "title": "Evolution of Trust",
        "description": """**Evolution of Trust (EOT)**

__1. Command__
- Run /eot on <@1291996619490984037>
- Queue the winner once the game ends
"""
    },
    "wordle": {
        "title": "Wordle",
        "description": """**Wordle**

__How to host__
- Type "new wordle"
- Ping event ping
- If there are multiple rounds, type "new wordle" once the word is guessed
- Keep track of the winners of each round
- Lock the channel (.l) and queue the winners at the end
"""
    },
    "rollkill": {
        "title": "Rollkill",
        "description": """**Rollkill**

__How to host__
- Run /rollkill on <@1291996619490984037> (number means the starting number people go from - use 1000000 unless otherwise specified | start means the amount of people that will be in the game)
- Once the game ends, queue the winner
"""
    },
    "auction": {
        "title": "Auction",
        "description": """**Auction**

__How to host__
- Accept an auction queued in <#1267530934723281009> by reacting with <:green_check:1218286675508199434>
- Bot will give donor player role, wait in <#1240782193270460476> for donation.
- Remove player role from donor and reply to donation embed with `-auction`
- Do `/itemcalc`, ping `auction ping` and unlock channel.
- Wait for bids and go once/twice/thrice as needed.
- Lock channel and do `-auction end`
- Wait for buyer donation.
- Queue auto-calculator amount for donor, and queue items for buyer.

- Auction troll bids/not paying will lead to a 1 week event blacklist
- Warn for troll bids (and reset price), failure to pay is 7d ebl (and a redo)
- EBLs for failure to pay can be removed early if the buyer decides to pay, they do not get the auction prize.

__Helpful commands__
- -auction set asset | changes the item people are auctioning for | ex: -auction set asset Watering Can
- -auction set buyer | changes the current buyer | ex: -auction set buyer <@739136309762850836>
- -auction set price | changes the highest bid | ex: -auction set price 15m
"""
    },
    "uno": {
        "title": "UNO",
        "description": """**Uno**

__How to host__
- Type uno join
- Use /giveaway create on <@530082442967646230> to start a 2 minute giveaway with 5 winners (unless otherwise specified)
- Ping event ping
- Type -uno to display uno rules
- Once the giveaway has finished, ask all the winners to type uno join before you type uno start
- You may warn for people who were afk and got autokicked from the game by the bot. There is currently no way to kick someone manually
- Once all of the winners have been determined, ask everyone to type uno quit, and then you can queue the winner(s)
"""
    },
    "gtn": {
        "title": "GTN",
        "description": """**GTN**

__How to host__
- Send the `-gtn [range]` command
- Set a 2-3s slowmode with `/slowmode`
- You will be dmed the number, do not tell anyone the answer or participate in the GTN
- Queue the prize for the winner once the game ends
- You may give hints if necessary
"""
    }
}

class RCEventGuideMenu(nextcord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(RCEventGuideSelect())

class RCEventGuideSelect(nextcord.ui.Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(
                label=menu["label"],
                description=menu["description"],
                value=menu["value"]
            ) for menu in EVENT_GUIDE_MENUS
        ]
        super().__init__(
            placeholder="Select an event guide...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: nextcord.Interaction):
        value = self.values[0]
        embed_info = EVENT_GUIDE_EMBEDS.get(value)
        if embed_info:
            embed = nextcord.Embed(
                title=embed_info["title"],
                description=embed_info["description"],
                color=nextcord.Color.blurple()
            )
            embed.set_footer(text="Created by the Robbing Central Admin Team", icon_url=interaction.guild.icon.url)
            embed.set_thumbnail(url=interaction.guild.icon.url)
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.response.send_message("No guide found for this selection.", ephemeral=True)

class RCEventGuide(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("RCEventGuide cog loaded")

    @commands.command(name="rceventguide", aliases=["recg"])
    async def rceventguide_cmd(self, ctx):
        embed = nextcord.Embed(
            title="RC Event Guide",
            description="For all event managers at Robbing Central, this guide is here to help you understand how events should be hosted here and the various guidelines that exist. If you are a new staff member, make sure to read the the General Event Guidelines thorougly before, and read the corresponding event's guide to the one you are hosting before hosting the event. If you see an event missing from here, please let an admin know so they can add it. If you have any questions about the event guide, please also ask an admin.\n\nCredit points for events are listed in the embed above this message.",
            color=nextcord.Color.blurple()
        )
        embed.set_footer(text="Created by the Robbing Central Admin Team", icon_url=ctx.guild.icon.url)
        embed.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed, view=RCEventGuideMenu())
        

def setup(bot):
    bot.add_cog(RCEventGuide(bot))
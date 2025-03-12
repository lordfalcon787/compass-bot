import nextcord
from nextcord.ext import commands
import asyncio
import json
from utils.mongo_connection import MongoConnection

VALID_CHANNELS = [1205270487454974061, 1214594429575503912, 1291161396368773183, 1219081468458831992, 1205270487274496054, 1229122015571476591]
RUMBLE_ROYALE = 693167035068317736
MAFIA = 758999095070687284
loading_emoji = "<a:loading_animation:1218134049780928584>"

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Items"]
configuration = db["Configuration"]

class MafiaModal(nextcord.ui.Modal):
    def __init__(self, bot, interaction, winners_list):
        super().__init__(
            "Prize",
            timeout=None,
        )

        self.event_name = nextcord.ui.TextInput(
            label="Prize Name",
            placeholder="Enter the Prize",
            min_length=1,
            max_length=30,
            required=True,
        )
        self.bot = bot
        self.interaction = interaction
        self.winners_list = winners_list
        self.add_item(self.event_name)

    async def callback(self, modal_interaction: nextcord.Interaction):
        await modal_interaction.response.defer(ephemeral=True)
        old_answer = self.event_name.value
        answer = old_answer.split(" ")
        try:
            ref = self.interaction.message.reference.cached_message
        except:
            ref_old = self.interaction.message.reference
            ref = self.bot.get_channel(ref_old.channel_id)
            ref = await ref.fetch_message(ref_old.message_id)
        if not ref:
            ref_old = self.interaction.message.reference
            ref = self.bot.get_channel(ref_old.channel_id)
            ref = await ref.fetch_message(ref_old.message_id)
        self.winners_list = await self.bot.get_cog("auto_queue").mafia_queue(ref)

        async def confirm_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal was_confirmed
            was_confirmed = True
            nonlocal msg
            winners = self.winners_list
            nonlocal item
            nonlocal quantity
            msg_id = self.interaction.message.reference.message_id
            embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for {len(winners)} winners.")
            embed.color = 65280
            embed.set_footer(text=f"This time may vary depending on the amount of winners.")
            await msg.edit(embed=embed, view=None)
            for winner in winners:
                winnerid = winner.replace("<", "").replace(">", "").replace("@", "")
                winnerid = int(winnerid)
                args = [winnerid, quantity, item, msg_id, "mafia"]
                await self.bot.get_cog("payouts").queue_payout(args, self.interaction)
            embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
            embed.color = 65280
            view = nextcord.ui.View()
            config = configuration.find_one({"_id": "config"})
            claim = config[f"claim"]
            claim = claim[f"{self.interaction.guild.id}"]
            view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{self.interaction.guild.id}/{claim}/"))
            await msg.edit(embed=embed, view=view)
            await ref.add_reaction(loading_emoji)
            try:
                await self.interaction.message.delete()
            except:
                pass

        async def cancel_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal msg
            nonlocal was_confirmed
            was_confirmed = True
            await msg.edit(content="Cancelled payout process.", embed=None, view=None)


        if len(answer) == 1:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return

            total_prize = quantity
            try:
                quantity = quantity // len(self.winners_list)
            except:
                await modal_interaction.send("Error calculating prize per winner. Please try again.", ephemeral=True)
                return
            
            if quantity == 0:
                await modal_interaction.send("Amount calculated per winner is equal to 0. Please try again with a valid amount.", ephemeral=True)
                return

            confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to queue ⏣ {quantity:,} for {len(self.winners_list)} winners?")
            confirmation_embed.add_field(name="Event", value="mafia")
            confirmation_embed.add_field(name="Winners", value="\n".join(self.winners_list))
            confirmation_embed.add_field(name="Prize per Winner", value=f"⏣ {quantity:,}")
            view = nextcord.ui.View()

            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)

            async def create_donor_callback(winner):
                async def donor_callback(interaction):
                    await interaction.response.defer(ephemeral=True)
                    nonlocal was_confirmed
                    was_confirmed = True
                    if winner in self.winners_list:
                        self.winners_list.remove(winner)
                        confirmation_embed.set_field_at(1, name="Winners", value="\n".join(self.winners_list))
                        nonlocal quantity
                        try:
                            quantity = total_prize // len(self.winners_list)
                        except:
                            await interaction.send("Error calculating prize per winner. Please try again.", ephemeral=True)
                            return
                        confirmation_embed.description = f"Are you sure you want to queue ⏣ {quantity:,} for {len(self.winners_list)} winners?"
                        confirmation_embed.set_field_at(2, name="Prize per Winner", value=f"⏣ {quantity:,}")
                        await msg.edit(embed=confirmation_embed)
                return donor_callback

            for winner in self.winners_list.copy():
                old_winner = winner
                winner = winner.replace("<", "").replace(">", "").replace("@", "")
                winner = int(winner)
                winner = await self.bot.fetch_user(winner)
                donor_button = nextcord.ui.Button(
                    label=f"Remove {winner.name}", 
                    style=nextcord.ButtonStyle.secondary,
                    custom_id=f"donor_{winner}"
                )
                donor_button.callback = await create_donor_callback(old_winner)
                view.add_item(donor_button)

            item = None
            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(15)
            if not was_confirmed:
                await msg.edit(content="No response within 15 seconds, process terminated.", embed=None, view=None)
        else:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return

            total_prize = quantity
            try:
                quantity = quantity // len(self.winners_list)
            except:
                await modal_interaction.send("Error calculating prize per winner. This may mean that the amount of the item entered is less than the amount of winners.", ephemeral=True)
                return
            
            if quantity == 0:
                await modal_interaction.send("Error calculating prize per winner. This may mean that the amount of the item entered is less than the amount of winners.", ephemeral=True)
                return

            item_choice = old_answer.replace(f"{answer[0]} ", "")
            item_collection = list(collection.find())
            item_choice = item_choice.lower()
            closest_item = None

            for item in item_collection:
                item_name = item["_id"].lower()
                if item_name == item_choice:
                    closest_item = item
                    break
            
                if len(item_choice.split(" ")) == 2 and len(item_name.split(" ")) == 2:
                    if item_choice.split(" ")[0] in item_name.split(" ")[0] and item_choice.split(" ")[1] in item_name.split(" ")[1]:
                        closest_item = item
                        break

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if all(word in item_name for word in item_choice.split()):
                        closest_item = item
                        break

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if item_choice.split(" ")[0] in item_name:
                        closest_item = item
                        break

            if not closest_item and len(item_choice.split(" ")) > 1:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if item_choice.split(" ")[1] in item_name:
                        closest_item = item
                        break

            if closest_item:
                item = closest_item["_id"]
            else:
                await modal_interaction.send(content="No matching item found. Please try again.", ephemeral=True)
                return
            
            confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to queue {quantity:,} {item} for {len(self.winners_list)} winners?")
            confirmation_embed.add_field(name="Event", value="mafia")
            confirmation_embed.add_field(name="Winners", value="\n".join(self.winners_list))
            confirmation_embed.add_field(name="Prize per Winner", value=f"{quantity:,} {item}")
            view = nextcord.ui.View()

            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)

            async def create_donor_callback(winner):
                async def donor_callback(interaction):
                    await interaction.response.defer(ephemeral=True)
                    nonlocal was_confirmed
                    was_confirmed = True
                    if winner in self.winners_list:
                        self.winners_list.remove(winner)
                        confirmation_embed.set_field_at(1, name="Winners", value="\n".join(self.winners_list))
                        nonlocal quantity
                        try:
                            quantity = total_prize // len(self.winners_list)
                        except:
                            await interaction.send("Error calculating prize per winner. Please try again.", ephemeral=True)
                            return
                        confirmation_embed.description = f"Are you sure you want to queue {quantity:,} {item} for {len(self.winners_list)} winners?"
                        confirmation_embed.set_field_at(2, name="Prize per Winner", value=f"{quantity:,} {item}")
                        await msg.edit(embed=confirmation_embed)
                return donor_callback

            for winner in self.winners_list.copy():
                old_winner = winner
                winner = winner.replace("<", "").replace(">", "").replace("@", "")
                winner = int(winner)
                winner = await self.bot.fetch_user(winner)
                donor_button = nextcord.ui.Button(
                    label=f"Remove {winner.name}", 
                    style=nextcord.ButtonStyle.secondary,
                    custom_id=f"donor_{winner}"
                )
                donor_button.callback = await create_donor_callback(old_winner)
                view.add_item(donor_button)

            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(15)
            if not was_confirmed:
                await msg.edit(content="No response within 15 seconds, process terminated.", embed=None, view=None)

class Modal(nextcord.ui.Modal):
    def __init__(self, bot, interaction):
        super().__init__(
            "Prize",
            timeout=300,
        )

        self.event_name = nextcord.ui.TextInput(
            label="Prize Name",
            placeholder="Enter the Prize",
            min_length=1,
            max_length=30,
            required=True,
        )
        self.bot = bot
        self.interaction = interaction
        self.add_item(self.event_name)

    async def callback(self, modal_interaction: nextcord.Interaction):
        await modal_interaction.response.defer(ephemeral=True)
        old_answer = self.event_name.value
        answer = old_answer.split(" ")
        ref = self.interaction.message.reference
        ref = ref.resolved
        ref_msg = ref
        ref = ref.mentions[0]

        async def confirm_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal msg
            winner = ref
            nonlocal item
            nonlocal quantity
            msg_id = self.interaction.message.reference.message_id
            args = [winner.id, quantity, item, msg_id, "rumble"]
            nonlocal was_confirmed
            was_confirmed = True
            embed = nextcord.Embed(description=f"<a:loading_animation:1218134049780928584> | Setting up payouts for 1 winner.")
            embed.set_footer(text=f"This time may vary depending on the amount of winners.")
            await msg.edit(embed=embed, view=None)
            await self.bot.get_cog("payouts").queue_payout(args, self.interaction)
            embed.description = f"<:green_check:1218286675508199434> | Payouts have been queued successfully."
            embed.color = 65280
            view = nextcord.ui.View()
            config = configuration.find_one({"_id": "config"})
            claim = config[f"claim"]
            claim = claim[f"{self.interaction.guild.id}"]
            view.add_item(nextcord.ui.Button(label="View Payouts", url=f"https://discord.com/channels/{self.interaction.guild.id}/{claim}/"))
            await msg.edit(embed=embed, view=view)
            await ref_msg.add_reaction(loading_emoji)
            await self.interaction.message.delete()

        async def cancel_callback(interaction):
            await interaction.response.defer(ephemeral=True)
            nonlocal msg
            nonlocal was_confirmed
            was_confirmed = True
            await msg.edit(content="Cancelled payout process.", embed=None, view=None)


        if len(answer) == 1:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return
            confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to queue {quantity}?")
            confirmation_embed.add_field(name="Event", value="rumble")
            confirmation_embed.add_field(name="Winner", value=ref.mention)
            confirmation_embed.add_field(name="Prize", value=f"{quantity:,}")
            view = nextcord.ui.View()
            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            item = None
            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(10)
            if not was_confirmed:
                await msg.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)
        else:
            multipliers = {'k': 1000, 'm': 1000000, 'b': 1000000000, 't': 1000000000000}
            quantity = answer[0].lower()
            if quantity[-1] in multipliers:
                try:
                    numeric_part = float(quantity[:-1])
                    multiplier = multipliers[quantity[-1]]
                    quantity = int(numeric_part * multiplier)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity format: {quantity}. Please use a number followed by k, m, b, or t.", ephemeral=True)
                    return
            else:
                if ',' in quantity:
                    quantity = quantity.replace(',', '')
                try:
                    quantity = int(quantity)
                except ValueError:
                    await modal_interaction.send(f"Invalid quantity: {quantity}. Please enter a number.", ephemeral=True)
                    return
            item_choice = old_answer.replace(f"{answer[0]} ", "")
            item_collection = list(collection.find())
            item_choice = item_choice.lower()
            closest_item = None

            for item in item_collection:
                item_name = item["_id"].lower()
                if item_name == item_choice:
                    closest_item = item
                    break
            
                if len(item_choice.split(" ")) == 2 and len(item_name.split(" ")) == 2:
                    if item_choice.split(" ")[0] in item_name.split(" ")[0] and item_choice.split(" ")[1] in item_name.split(" ")[1]:
                        closest_item = item
                        break

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if all(word in item_name for word in item_choice.split()):
                        closest_item = item
                        break

            if not closest_item:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if item_choice.split(" ")[0] in item_name:
                        closest_item = item
                        break

            if not closest_item and len(item_choice.split(" ")) > 1:
                for item in item_collection:
                    item_name = item["_id"].lower()
                    if item_choice.split(" ")[1] in item_name:
                        closest_item = item
                        break

            if closest_item:
                item = closest_item["_id"]
            else:
                await msg.edit(content="No matching item found. Please try again.")
                return
            
            confirmation_embed = nextcord.Embed(title="Confirm Payouts", description=f"Are you sure you want to queue {quantity:,} {item}?")
            confirmation_embed.add_field(name="Event", value="rumble")
            confirmation_embed.add_field(name="Winner", value=ref.mention)
            confirmation_embed.add_field(name="Prize", value=f"{quantity:,} {item}")
            view = nextcord.ui.View()
            confirm_button = nextcord.ui.Button(label="Confirm", style=nextcord.ButtonStyle.success, custom_id="auto_queue_confirm")
            cancel_button = nextcord.ui.Button(label="Cancel", style=nextcord.ButtonStyle.danger, custom_id="auto_queue_cancel")
            confirm_button.callback = confirm_callback
            cancel_button.callback = cancel_callback
            view.add_item(confirm_button)
            view.add_item(cancel_button)
            was_confirmed = False
            msg = await modal_interaction.send(embed=confirmation_embed, ephemeral=True, view=view)
            await asyncio.sleep(10)
            if not was_confirmed:
                await msg.edit(content="No response within 10 seconds, process terminated.", embed=None, view=None)


    def calculate_match_score(self, item_name, user_input):
        item_name = item_name.lower()
        user_input = user_input.lower()
        
        if item_name == user_input:
            return 0
            
        item_words = item_name.split()
        input_words = user_input.split()
        
        all_words_match = all(any(input_word in item_word or item_word in input_word
                                for item_word in item_words)
                            for input_word in input_words)
                            
        if all_words_match:
            return 1 + abs(len(item_name) - len(user_input)) / 100
            
        max_len = max(len(item_name), len(user_input))
        return 100 + sum(1 for i in range(max_len) if i >= len(item_name)
                        or i >= len(user_input)
                        or item_name[i] != user_input[i])       

class QueueThis(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        button = nextcord.ui.Button(label="Queue This?", style=nextcord.ButtonStyle.primary, custom_id="auto_queue_confirm")
        button.callback = self.auto_queue_confirm
        self.add_item(button)

    async def auto_queue_confirm(self, interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        winners_list = None
        try:
            await interaction.response.send_modal(MafiaModal(self.bot, interaction, winners_list))
        except Exception as e:
            print(f"Error in auto_queue_confirm: {e}")
            return
        
class QueueThisRumble(nextcord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot
        
        button = nextcord.ui.Button(label="Queue This?", style=nextcord.ButtonStyle.primary, custom_id="auto_queue_rumble_confirm")
        button.callback = self.auto_queue_confirm
        self.add_item(button)

    async def auto_queue_confirm(self, interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
            return
        try:
            await interaction.response.send_modal(Modal(self.bot, interaction))
        except:
            return
    
class auto_queue(commands.Cog): 
    def __init__(self, bot):
        self.bot = bot


    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(QueueThis(self.bot))
        self.bot.add_view(QueueThisRumble(self.bot))
        print("Auto Queue Cog is ready.")


    @commands.command(name="test_result")
    async def test_result(self, ctx):
        item_collection = list(collection.find())
        item_choice = ctx.message.content.lower()
        item_choice = item_choice.replace("test_result ", "")
        item_choice = item_choice.replace("!", "").replace("-", "").replace(".", "")
        item_choice = item_choice.lower()
        closest_item = None

        for item in item_collection:
            item_name = item["_id"].lower()
            if item_name == item_choice:
                closest_item = item
                break
            
            if len(item_choice.split(" ")) == 2 and len(item_name.split(" ")) == 2:
                if item_choice.split(" ")[0] in item_name.split(" ")[0] and item_choice.split(" ")[1] in item_name.split(" ")[1]:
                    closest_item = item
                    break

        if not closest_item:
            for item in item_collection:
                item_name = item["_id"].lower()
                if all(word in item_name for word in item_choice.split()):
                    closest_item = item
                    break

        if not closest_item:
            for item in item_collection:
                item_name = item["_id"].lower()
                if item_choice.split(" ")[0] in item_name:
                    closest_item = item
                    break

        if not closest_item and len(item_choice.split(" ")) > 1:
            for item in item_collection:
                item_name = item["_id"].lower()
                if item_choice.split(" ")[1] in item_name:
                    closest_item = item
                    break

        if not closest_item:
            await ctx.send("No matching item found. Please try again.")
            return

        item = closest_item["_id"]
        await ctx.send(f"Closest item found: {item}")

    async def daily_rumble(self, message):
        winner = message.mentions[0]
        await message.add_reaction(loading_emoji)
        await self.bot.get_cog("payouts").queue_payout([winner.id, 10000000, None, message.id, "daily rumble"], message)

    async def mafia_queue(self, message):
        try:
            embed = message.embeds[0]
            fields = embed.fields
            winners = fields[0].value.lower()
            winners_list = []
            winners = winners.replace("_", "").replace("*", "")
            if "other winners" not in winners:
                winners = winners.replace("main winners", "")
                if "\n\n" in winners:
                    winners = winners.split("\n\n")[0]
                winners = winners.split("\n")
                for line in winners:
                    if "-" in line:
                        mention = line.split(" ")[1].strip()
                        winners_list.append(mention)
                if not winners_list:
                    return None
            else:
                main_winners = winners.split("other winners")[0]
                main_winners = main_winners.replace("main winners", "")
                other_winners = winners.split("other winners")[1]
                if "\n\n" in main_winners:
                    main_winners = main_winners.split("\n\n")[0]
                main_winners = main_winners.split("\n")
                for line in main_winners:
                    if "-" in line:
                        mention = line.split(" ")[1].strip()
                        winners_list.append(mention)
                for line in other_winners.split("\n"):
                    if "-" in line:
                        mention = line.split(" ")[1].strip()
                        winners_list.append(mention)
                if not winners_list:
                    return None
            if message.channel.id == 1346932927937904743:
                asyncio.create_task(self.check_eligibility(message, winners_list))
            return winners_list
        except Exception as e:
            print(f"Error in mafia_queue: {e}")
            return
        
    async def check_eligibility(self, message, winners_list):        
        wrongwinners = []

        for winner_ in winners_list:
            winner_ = winner_.replace("<@", "").replace(">", "")
            if winner_.isdigit():
                user = message.guild.get_member(int(winner_))
                if not user:
                    continue
                try:
                    user_roles = [role.id for role in user.roles]
                    if 1346933199925674086 not in user_roles and 1205270486469058637 not in user_roles:
                        wrongwinners.append(user.id)
                except AttributeError:
                    continue

        if wrongwinners:
            descp = "\n".join(f"{i+1}. <@{winner}>" for i, winner in enumerate(wrongwinners))
            embed = nextcord.Embed(title="Invalid Winners Detected", description=descp, color=nextcord.Color.red())
            await message.reply(embed=embed)

    async def mafia_reminder(self, message):
        msg = None
        try:
            async with asyncio.timeout(4):
                async for message in message.channel.history(limit=20):
                    if message.author.id == MAFIA:
                        if "executing command...." in message.content.lower():
                            msg = message
                            break
        except asyncio.TimeoutError:
            return
        if msg:
            con = msg.content
            con = con.replace("Executing command.... Ran by ", "")
            con = con.replace("<", "").replace(">", "").replace("@", "")
            con = int(con)
            await msg.reply(content=f"<@{con}> your mafia game has ended.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.channel.id == 1205669368697065532 and message.author.id == RUMBLE_ROYALE:
            if not message.embeds:
                return
            elif not message.embeds[0].title:
                return
            elif "winner" not in message.embeds[0].title.lower():
                return
            await self.daily_rumble(message)
            return        
        elif message.author.id == RUMBLE_ROYALE:
            if not message.embeds:
                return
            elif not message.embeds[0].title:
                return
            elif "winner" not in message.embeds[0].title.lower():
                return
            elif message.embeds[0].fields and "Dank Memer" in message.embeds[0].fields[0].name:
                return
            config = configuration.find_one({"_id": "config"})
            guild_id = str(message.guild.id)
            claim = config[f"claim"]
            queue = config[f"queue"]
            payout = config[f"payout"]
            root = config[f"root"]
            if guild_id not in claim or guild_id not in queue or guild_id not in payout or guild_id not in root:
                return
            view = QueueThisRumble(self.bot)
            await message.reply(view=view)
        elif message.author.id == MAFIA or message.author.id == 204255221017214977:
            if not message.embeds:
                return
            elif not message.embeds[0].title:
                return
            elif message.channel.name == "mafia":
                return
            elif "game over" not in message.embeds[0].title.lower():
                return
            config = configuration.find_one({"_id": "config"})
            guild_id = str(message.guild.id)
            claim = config[f"claim"]
            queue = config[f"queue"]
            payout = config[f"payout"]
            root = config[f"root"]
            if guild_id not in claim or guild_id not in queue or guild_id not in payout or guild_id not in root:
                return
            view = QueueThis(self.bot)
            await message.reply(view=view)
            await self.mafia_reminder(message)
            return
        else:
            return
        

def setup(bot):
    bot.add_cog(auto_queue(bot))
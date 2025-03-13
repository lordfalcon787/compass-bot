import nextcord

from nextcord import SlashOption
from nextcord.ext import commands
from googletrans import Translator

LANG_CODES = {
        "en": "English", "es": "Spanish", "zh-cn": "Chinese", 
        "hi": "Hindi", "ar": "Arabic", "pt": "Portuguese",
        "ru": "Russian", "ja": "Japanese", "de": "German", 
        "fr": "French", "tr": "Turkish", "ko": "Korean",
        "it": "Italian", "vi": "Vietnamese", "pl": "Polish",
        "nl": "Dutch", "th": "Thai", "id": "Indonesian",
        "fa": "Persian", "ms": "Malay", "sv": "Swedish",
        "el": "Greek", "ro": "Romanian", "cs": "Czech",
        "he": "Hebrew"
    }

class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Translate cog loaded")

    @commands.command(name="translate")
    async def translate(self, ctx):
        print("-1")
        try:
            print("0")
            translator = Translator()
            print("1")
            message_to_translate = ""
            if ctx.message.reference and ctx.message.reference.resolved:
                print("2")
                message_to_translate = ctx.message.reference.resolved.content
                if message_to_translate == "":
                    await ctx.reply("Please provide a valid message to translate.", mention_author=False)
                    return
            else:
                print("3")
                message_to_translate = ctx.message.content.replace(f"{ctx.prefix}translate", "", 1).strip()
                if message_to_translate == "":
                    await ctx.reply("Please provide a valid message to translate.", mention_author=False)
                    return
            print("4")
            if message_to_translate == "":
                await ctx.reply("Please provide a valid message to translate.", mention_author=False)
                return
            print("5")
            english = translator.translate(message_to_translate, dest="en")
            print("6")
            spanish = translator.translate(message_to_translate, dest="es")
            print("7")
            chinese = translator.translate(message_to_translate, dest="zh-cn")
            print("8")
            detection_lang = LANG_CODES.get(english.src, english.src.capitalize())
            print("9")
            embed = nextcord.Embed(title="Translation", color=0x3498db)
            print("10")
            embed.add_field(
                name=f"Original ({detection_lang})",
                value=message_to_translate,
                inline=False
            )
            print("11")
            embed.add_field(
                name="Translation (English)",
                value=english.text,
                inline=False
            )
            print("12")
            embed.add_field(
                name="Translation (Spanish)",
                value=spanish.text,
                inline=False
            )
            print("13")
            embed.add_field(
                name="Translation (Chinese)",
                value=chinese.text,
                inline=False
            )
            print("14")
            await ctx.send(embed=embed)
            print("15")
        except Exception as e:
            print("16")
            await ctx.send(f"An error occurred while translating: {str(e)}")

    @nextcord.slash_command(name="translate", description="Translate a message to a different language.")
    async def translate(self, interaction: nextcord.Interaction, 
                       message: str, 
                       to_language: str = SlashOption(
                           description="The language to translate the message to.", 
                           choices={"English": "en", "Spanish": "es", "Chinese": "zh-cn", 
                                  "Hindi": "hi", "Arabic": "ar", "Portuguese": "pt",
                                  "Russian": "ru", "Japanese": "ja", "German": "de", 
                                  "French": "fr", "Turkish": "tr", "Korean": "ko",
                                  "Italian": "it", "Vietnamese": "vi", "Polish": "pl",
                                  "Dutch": "nl", "Thai": "th", "Indonesian": "id",
                                  "Persian": "fa", "Malay": "ms", "Swedish": "sv",
                                  "Greek": "el", "Romanian": "ro", "Czech": "cs",
                                  "Hebrew": "he"},
                           required=False,
                           default="English"
                       )):
        try:
            await interaction.response.defer(ephemeral=True)
            translator = Translator()
            
            translation = await translator.translate(message, dest=to_language)
            
            from_lang = LANG_CODES.get(translation.src, translation.src.capitalize())
            to_lang = LANG_CODES.get(to_language, to_language.capitalize())
            
            embed = nextcord.Embed(title="Translation", color=0x3498db)
            embed.add_field(
                name=f"Original ({from_lang})", 
                value=message, 
                inline=False
            )
            embed.add_field(
                name=f"Translation ({to_lang})", 
                value=translation.text, 
                inline=False
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(
                f"An error occurred while translating: {str(e)}", 
                ephemeral=True
            )

def setup(bot: commands.Bot):
    bot.add_cog(Translate(bot))

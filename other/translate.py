import nextcord
from nextcord import SlashOption
from nextcord.ext import commands
from googletrans import Translator

class Translate(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Translate cog loaded")

    @commands.command(name="translate")
    async def translate(self, ctx: commands.Context):
        try:
            translator = Translator()
            
            if ctx.message.reference and ctx.message.reference.resolved:
                message_to_translate = ctx.message.reference.resolved.content
            else:
                message_to_translate = ctx.message.content.replace(f"{ctx.prefix}translate", "", 1).strip()
                if not message_to_translate:
                    await ctx.send("Please provide a message to translate or reply to a message.")
                    return
            
            detection = await self.bot.loop.run_in_executor(
                None,
                lambda: translator.detect(message_to_translate)
            )
            
            translations = {}
            for lang_code, lang_name in [("en", "English"), ("es", "Spanish"), ("zh-cn", "Chinese")]:
                if lang_code != detection.lang:
                    translation = await self.bot.loop.run_in_executor(
                        None,
                        lambda: translator.translate(message_to_translate, dest=lang_code)
                    )
                    translations[lang_name] = translation.text
            
            embed = nextcord.Embed(title="Translation", color=0x3498db)
            embed.add_field(
                name=f"Original ({detection.lang.upper()})",
                value=message_to_translate,
                inline=False
            )
            
            for lang_name, translated_text in translations.items():
                embed.add_field(
                    name=f"Translation ({lang_name})",
                    value=translated_text,
                    inline=False
                )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
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
            
            def do_translation():
                return translator.translate(message, dest=to_language)
            
            translation = await self.bot.loop.run_in_executor(None, do_translation)
            
            embed = nextcord.Embed(title="Translation", color=0x3498db)
            embed.add_field(
                name=f"Original ({translation.src.upper()})", 
                value=message, 
                inline=False
            )
            embed.add_field(
                name=f"Translation ({to_language})", 
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

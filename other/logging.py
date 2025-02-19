import nextcord
from nextcord.ext import commands
from datetime import datetime

from utils.mongo_connection import MongoConnection

mongo = MongoConnection.get_instance()
db = mongo.get_db()
collection = db["Logging"]

class Logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        print("Logging cog loaded.")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return
        
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{message.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Message Deleted",
                description=f"A message by {message.author.mention} was deleted in {message.channel.mention}",
                color=nextcord.Color.red()
            )
            embed.add_field(
                name="Deleted Message",
                value=(message.content[:1000] + "...") if len(message.content) > 1000 else (message.content or "No content"),
                inline=False
            )
            embed.set_author(
                name=message.author.name,
                icon_url=message.author.avatar.url if message.author.avatar else message.author.default_avatar.url
            )
            embed.set_footer(text=f"User ID: {message.author.id} | Channel ID: {message.channel.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot or before.content == after.content:
            return
        
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{before.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Message Edited",
                description=f"A message by {before.author.mention} was edited in {before.channel.mention}",
                color=nextcord.Color.orange()
            )
            embed.add_field(
                name="Before",
                value=(before.content[:1000] + "...") if len(before.content) > 1000 else (before.content or "No content"),
                inline=False
            )
            embed.add_field(
                name="After",
                value=(after.content[:1000] + "...") if len(after.content) > 1000 else (after.content or "No content"),
                inline=False
            )
            embed.set_author(
                name=before.author.name,
                icon_url=before.author.avatar.url if before.author.avatar else before.author.default_avatar.url
            )
            embed.set_footer(text=f"User ID: {before.author.id} | Channel ID: {before.channel.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_member_join(self, member):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{member.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Member Joined",
                description=f"{member.mention} has joined the server",
                color=nextcord.Color.green()
            )
            try:
                embed.set_thumbnail(url=member.avatar.url)
            except:
                pass
            embed.add_field(name="Account Created", value=member.created_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{member.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Member Left",
                description=f"{member.mention} has left the server",
                color=nextcord.Color.red()
            )
            try:
                embed.set_thumbnail(url=member.avatar.url)
            except:
                pass
            embed.add_field(name="Joined Server", value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S UTC"), inline=False)
            embed.set_footer(text=f"User ID: {member.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{channel.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Channel Created",
                description=f"A new channel {channel.mention} was created",
                color=nextcord.Color.blue()
            )
            embed.add_field(name="Channel Type", value=str(channel.type), inline=False)
            embed.set_footer(text=f"Channel ID: {channel.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{channel.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Channel Deleted",
                description=f"A channel named '{channel.name}' was deleted",
                color=nextcord.Color.red()
            )
            embed.add_field(name="Channel Type", value=str(channel.type), inline=False)
            embed.set_footer(text=f"Channel ID: {channel.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{role.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Role Created",
                description=f"A new role {role.mention} was created",
                color=nextcord.Color.green()
            )
            embed.add_field(name="Role Name", value=role.name, inline=True)
            embed.add_field(name="Role Color", value=str(role.color), inline=True)
            embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
            embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
            embed.set_footer(text=f"Role ID: {role.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener() 
    async def on_guild_role_delete(self, role):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{role.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            embed = nextcord.Embed(
                title="Role Deleted",
                description=f"A role named '{role.name}' was deleted",
                color=nextcord.Color.red()
            )
            embed.add_field(name="Role Color", value=str(role.color), inline=True)
            embed.add_field(name="Hoisted", value=str(role.hoist), inline=True)
            embed.add_field(name="Mentionable", value=str(role.mentionable), inline=True)
            embed.set_footer(text=f"Role ID: {role.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{before.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            if before.name == after.name and before.color == after.color and before.hoist == after.hoist and before.mentionable == after.mentionable and before.permissions == after.permissions:
                return

            embed = nextcord.Embed(
                title="Role Updated",
                description=f"The role {after.mention} was updated",
                color=nextcord.Color.blue()
            )
            
            if before.name != after.name:
                embed.add_field(name="Name Changed", value=f"From: {before.name}\nTo: {after.name}", inline=False)
            
            if before.color != after.color:
                embed.add_field(name="Color Changed", value=f"From: {before.color}\nTo: {after.color}", inline=False)
                
            if before.hoist != after.hoist:
                embed.add_field(name="Hoisted Changed", value=f"From: {before.hoist}\nTo: {after.hoist}", inline=False)
                
            if before.mentionable != after.mentionable:
                embed.add_field(name="Mentionable Changed", value=f"From: {before.mentionable}\nTo: {after.mentionable}", inline=False)
                
            if before.permissions != after.permissions:
                changed_perms = []
                for perm, value in after.permissions:
                    if value != getattr(before.permissions, perm):
                        changed_perms.append(f"{perm}: {getattr(before.permissions, perm)} → {value}")
                if changed_perms:
                    embed.add_field(name="Permissions Changed", value="\n".join(changed_perms), inline=False)
                    
            embed.set_footer(text=f"Role ID: {after.id}")
            
            await logging_channel.send(embed=embed)
        except:
            return

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles == after.roles:
            return
            
        try:
            channel_id = int(collection.find_one({"_id": "data"})[f"{before.guild.id}"])
            logging_channel = self.bot.get_channel(channel_id)
            if not logging_channel:
                return
            
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if not added_roles and not removed_roles:
                return

            embed = nextcord.Embed(
                title="Member Roles Updated",
                description=f"Roles were modified for {after.mention}",
                color=nextcord.Color.blue()
            )

            if added_roles:
                embed.add_field(
                    name="Roles Added", 
                    value=", ".join([role.mention for role in added_roles]),
                    inline=False
                )

            if removed_roles:
                embed.add_field(
                    name="Roles Removed",
                    value=", ".join([role.mention for role in removed_roles]), 
                    inline=False
                )

            embed.set_author(
                name=after.name,
                icon_url=after.avatar.url if after.avatar else after.default_avatar.url
            )
            embed.set_footer(text=f"User ID: {after.id}")

            await logging_channel.send(embed=embed)
        except:
            return

def setup(bot):
    bot.add_cog(Logging(bot))
import discord
from discord.ext import commands
from discord.ui import View, Button
from config import TOKEN, PREFIX, LOG_CHANNEL_ID, SUPPORT_ROLE_ID, COMMAND_ROLE_ID
from keep_alive import keep_alive  # Importation de la fonction keep_alive
import sys
import os
import asyncio

# Ajouter le répertoire courant au chemin de recherche
sys.path.append(os.getcwd())  # Cela ajoute le répertoire actuel au chemin de recherche de Python

# Démarrer le serveur web pour garder le bot en ligne
keep_alive()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

# ⚠️ Désactivation de la commande help par défaut
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)

# ✅ Check personnalisé pour le rôle autorisé
def has_required_role():
    async def predicate(ctx):
        return discord.utils.get(ctx.author.roles, id=COMMAND_ROLE_ID) is not None
    return commands.check(predicate)

# 🎟️ View avec les boutons du ticket
class TicketButtons(View):
    def __init__(self, author):
        super().__init__(timeout=None)
        self.author = author

    @discord.ui.button(label="Fermer le ticket", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            await log_channel.send(f"📁 Ticket fermé : {interaction.channel.name} par {interaction.user.mention}")
        await interaction.channel.delete()

    @discord.ui.button(label="Ajouter rôle", style=discord.ButtonStyle.success)
    async def add_role(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(SUPPORT_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(f"✅ Rôle {role.name} ajouté à {interaction.user.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message("Rôle introuvable (vérifie l'ID dans config.py).", ephemeral=True)

    @discord.ui.button(label="Ping l'utilisateur", style=discord.ButtonStyle.primary)
    async def ping_user(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🔔 {self.author.mention}, on s'occupe de toi !",
            allowed_mentions=discord.AllowedMentions(users=True)
        )

class TicketOpener(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🎫 Ouvrir un ticket", style=discord.ButtonStyle.success)
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        ticket_channel = await guild.create_text_channel(f"ticket-{interaction.user.name}", overwrites=overwrites)
        embed = discord.Embed(
            title="🎫 Ticket Ouvert",
            description="Bienvenue ! Un membre du staff va bientôt vous aider.",
            color=0x00ff00
        )
        await ticket_channel.send(content=f"{interaction.user.mention}", embed=embed, view=TicketButtons(interaction.user))
        await interaction.response.send_message(f"✅ Ton ticket a été ouvert ici : {ticket_channel.mention}", ephemeral=True)

# Définir les commandes du bot
class Commands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @has_required_role()
    async def ping(self, ctx):
        await ctx.send("Pong! 🏓")

    @commands.command()
    @has_required_role()
    async def crown(self, ctx):
        await ctx.send("👑 The power is mine!")

    @commands.command()
    @has_required_role()
    async def lock(self, ctx):
        role = discord.utils.get(ctx.guild.roles, id=SUPPORT_ROLE_ID)
        if role:
            await ctx.channel.set_permissions(role, send_messages=False)
            await ctx.send(f"🔒 Channel locked for {role.mention}")
        else:
            await ctx.send("Role not found.")

    @commands.command()
    @has_required_role()
    async def unlock(self, ctx):
        role = discord.utils.get(ctx.guild.roles, id=SUPPORT_ROLE_ID)
        if role:
            await ctx.channel.set_permissions(role, send_messages=True)
            await ctx.send(f"🔓 Channel unlocked for {role.mention}")
        else:
            await ctx.send("Role not found.")

    @commands.command()
    @has_required_role()
    async def transcript(self, ctx):
        messages = []
        async for message in ctx.channel.history(limit=100):
            messages.append(f"[{message.created_at}] {message.author}: {message.content}")
        messages.reverse()

        filename = f"transcript-{ctx.channel.name}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(messages))

        await ctx.send(file=discord.File(filename))

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def setlog(self, ctx, channel: discord.TextChannel):
        global LOG_CHANNEL_ID
        LOG_CHANNEL_ID = channel.id
        await ctx.send(f"📒 Log channel set to {channel.mention}")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def addrole(self, ctx, member: discord.Member, *, role_name):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await member.add_roles(role)
            await ctx.send(f"✅ Role {role.name} added to {member.mention}.")
        else:
            await ctx.send("Role not found.")

    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def removerole(self, ctx, member: discord.Member, *, role_name):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role:
            await member.remove_roles(role)
            await ctx.send(f"❌ Role {role.name} removed from {member.mention}.")
        else:
            await ctx.send("Role not found.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def createsalon(self, ctx, *, name):
        await ctx.guild.create_text_channel(name)
        await ctx.send(f"✅ Channel #{name} created.")

    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def deletesalon(self, ctx, *, name):
        channel = discord.utils.get(ctx.guild.text_channels, name=name)
        if channel:
            await channel.delete()
            await ctx.send(f"🗑️ Channel #{name} deleted.")
        else:
            await ctx.send("Channel not found.")

    @commands.command()
    @has_required_role()
    async def renamesalon(self, ctx, *, new_name: str):
        if ctx.message.channel.type == discord.ChannelType.text:
            await ctx.channel.edit(name=new_name)
            await ctx.send(f"✅ Le salon a été renommé en : {new_name}")
        else:
            await ctx.send("❌ Cette commande ne peut être utilisée que dans un salon textuel.")

    @commands.command()
    @has_required_role()
    async def help(self, ctx):
        embed = discord.Embed(
            title="📖 Available Commands",
            description="Here is the list of commands you can use:",
            color=0xbb00ff
        )
        embed.add_field(name="!ping", value="Replies with Pong!", inline=False)
        embed.add_field(name="!crown", value="Show your royal power 👑", inline=False)
        embed.add_field(name="!lock", value="Locks the channel for a specific role", inline=False)
        embed.add_field(name="!unlock", value="Unlocks the channel for a specific role", inline=False)
        embed.add_field(name="!transcript", value="Records the channel's history", inline=False)
        embed.add_field(name="!setlog #channel", value="Sets the log channel", inline=False)
        embed.add_field(name="!addrole @member Role", value="Adds a role to a member", inline=False)
        embed.add_field(name="!removerole @member Role", value="Removes a role from a member", inline=False)
        embed.add_field(name="!createsalon name", value="Creates a text channel", inline=False)
        embed.add_field(name="!deletesalon name", value="Deletes a text channel", inline=False)
        embed.add_field(name="!renamesalon name", value="Renames the current text channel", inline=False)
        embed.add_field(name="!mute @member", value="Mutes a member with the Muted role", inline=False)
        embed.add_field(name="!unmute @member", value="Unmutes a member (removes Muted role)", inline=False)
        embed.add_field(name="!ticket", value="Creates a private support channel", inline=False)
        embed.add_field(name="!stat", value="Displays server statistics", inline=False)
        embed.add_field(name="!createrole Name permission1 permission2 ...", value="Creates a role with custom permissions", inline=False)
        embed.add_field(name="!payements", value="Displays the classic PayPal link", inline=False)
        embed.add_field(name="!payementsinter", value="Displays the international PayPal link", inline=False)
        embed.add_field(name="!help", value="Displays this help message", inline=False)
        embed.set_footer(text="Crown Bot • Royal Assistance 🤴")
        await ctx.send(embed=embed)

    @commands.command()
    @has_required_role()
    async def stat(self, ctx):
        guild = ctx.guild
        total_members = guild.member_count
        boosts = guild.premium_subscription_count
        boosters = sum(1 for member in guild.members if member.premium_since)

        embed = discord.Embed(
            title=f"📊 Server Statistics: {guild.name}",
            color=0xbb00ff
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)

        embed.add_field(name="👥 Members", value=f"{total_members}", inline=True)
        embed.add_field(name="🚀 Boosts", value=f"{boosts}", inline=True)
        embed.add_field(name="🌟 Boosters", value=f"{boosters}", inline=True)
        embed.set_footer(text=f"Server ID: {guild.id}")

        await ctx.send(embed=embed)

# ⚙️ Setup async requis
async def setup(bot):
    await bot.add_cog(Commands(bot))
    await bot.add_cog(Tickets(bot))  # Ajout du cog de tickets
    bot.add_view(TicketOpener())  # Important pour que les boutons fonctionnent même après restart

# Lancer le bot
async def main():
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())

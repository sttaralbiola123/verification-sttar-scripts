import discord
import os
import asyncio
import requests
from database import get_guild, get_user, save_guild

intents = discord.Intents.default()
intents.members = True

bot = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(bot)

async def verify_member(discord_id: str, guild_id: str):
    try:
        guild = bot.get_guild(int(guild_id))
        if not guild: return False
        member = guild.get_member(int(discord_id)) or await guild.fetch_member(int(discord_id))
        if not member: return False

        data = get_guild(guild_id)
        not_role = guild.get_role(int(data['not_verified_role_id']))
        ver_role = guild.get_role(int(data['verified_role_id']))

        if not_role: await member.remove_roles(not_role)
        if ver_role: await member.add_roles(ver_role)
        return True
    except Exception as e:
        print(f"Role error: {e}")
        return False

async def re_add_member(discord_id: str):
    await asyncio.sleep(20 * 60)  # 20 minutes
    user = get_user(discord_id)
    if not user or not user.get('access_token'): return

    try:
        guild = bot.get_guild(int(user['guild_id']))
        if guild and not guild.get_member(int(discord_id)):
            url = f"https://discord.com/api/v10/guilds/{user['guild_id']}/members/{discord_id}"
            headers = {"Authorization": f"Bot {os.getenv('BOT_TOKEN')}"}
            data = {"access_token": user['access_token']}
            requests.put(url, json=data, headers=headers)
            print(f"✅ Auto rejoined: {discord_id}")
    except Exception as e:
        print(f"Rejoin failed: {e}")

@bot.event
async def on_ready():
    print(f"✅ Bot is Online: {bot.user}")
    await tree.sync()

@bot.event
async def on_member_join(member):
    await asyncio.sleep(2)
    data = get_guild(str(member.guild.id))
    if data and data.get('not_verified_role_id'):
        role = member.guild.get_role(int(data['not_verified_role_id']))
        if role:
            await member.add_roles(role)

@bot.event
async def on_member_remove(member):
    if get_user(str(member.id)):
        print(f"👋 {member} left - Will try to rejoin in 20 minutes")
        asyncio.create_task(re_add_member(str(member.id)))

@tree.command(name="setup", description="Setup verification system")
@discord.app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    guild = interaction.guild
    guild_id = str(guild.id)

    not_role = await guild.create_role(name="Not Verified", color=discord.Color.red())
    ver_role = await guild.create_role(name="✅ Verified", color=discord.Color.green())

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=True, send_messages=False),
        guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        ver_role: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }

    channel = await guild.create_text_channel("✅-verification", overwrites=overwrites)
    save_guild(guild_id, str(channel.id), str(not_role.id), str(ver_role.id), str(interaction.user.id))

    embed = discord.Embed(title="🔐 Verification Required", description="Click the button to verify.", color=0x5865f2)
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="Verify Now",
        url="https://verification-sttar-scripts.onrender.com/login?guild_id=" + guild_id,
        style=discord.ButtonStyle.green,
        emoji="✅"
    ))

    await channel.send(embed=embed, view=view)
    await interaction.followup.send(f"✅ Setup Complete! Channel: {channel.mention}", ephemeral=True)

import discord
from src import config

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(int(config.DISCORD_GUILD_ID))
    if guild:
        for role in guild.roles:
            print(f"Role: {role.name} | ID: {role.id}")
    else:
        print("Không tìm thấy guild")
    await client.close()

client.run(config.DISCORD_TOKEN)

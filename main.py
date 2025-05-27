import nextcord
from nextcord.ext import commands
import json
import os
from cogs.topup import TopupView  # Assuming TopupView is defined in topup.py


with open('config.json', 'r', encoding='utf-8') as file:
    config = json.load(file)


bot = commands.Bot(command_prefix='!', intents=nextcord.Intents.all())


for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        extension = f'cogs.{filename[:-3]}'
        try:
            bot.load_extension(extension)
            print(f'Loaded extension {extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}: {e}')

@bot.event
async def on_ready():
    await bot.sync_all_application_commands()
    print(f"✅ Synced application commands")

    guild = bot.get_guild(int(config["guild"]))  # ✅ ใช้ key เป็นสตริง

    if guild:
        bot.add_view(TopupView(bot, guild))
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    bot.add_view(TopupView(bot, guild))
    print("✅ Persistent view added.")


bot.run(config['token'])
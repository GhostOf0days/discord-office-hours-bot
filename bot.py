import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

import utils

load_dotenv()

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=None, intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    print('------')
    await utils.load_cogs(bot)
    await bot.tree.sync()

bot.run(os.getenv('DISCORD_TOKEN'))
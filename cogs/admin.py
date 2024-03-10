import discord
from discord.ext import commands
from discord import app_commands

import config

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @app_commands.command(name='reload', description='Reload all extensions')
    @app_commands.checks.has_role(config.ADMIN_ROLE)
    async def reload(self, interaction: discord.Interaction):
        for filename in os.listdir('./cogs'):
            if filename.endswith('.py'):
                await self.bot.reload_extension(f'cogs.{filename[:-3]}')
        await interaction.response.send_message('Reloaded all extensions')

async def setup(bot):
    await bot.add_cog(Admin(bot))
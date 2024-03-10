import discord
from discord.ext import commands, tasks
from discord import app_commands

import config
import utils
from datetime import datetime, timedelta

class Queue(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue_data = utils.load_queue_data()
        self.check_queue_timeout.start()
        
    @app_commands.command(name='join', description='Join the queue')
    async def join(self, interaction: discord.Interaction, contact_info: str):
        user_id = str(interaction.user.id)
        
        if user_id in self.queue_data:
            await interaction.response.send_message('You are already in the queue!', ephemeral=True)
            return
            
        self.queue_data[user_id] = {
            "user_id": user_id,
            "name": interaction.user.display_name,
            "contact_info": contact_info,
            "join_time": datetime.now().isoformat(),
            "helped_by": None,
            "help_start_time": None,
            "help_end_time": None
        }
        utils.save_queue_data(self.queue_data)
        
        queue_channel = interaction.guild.get_channel(config.QUEUE_CHANNEL)
        await queue_channel.send(f'{interaction.user.mention} has joined the queue!')
        await interaction.response.send_message('You have been added to the queue!', ephemeral=True)
        
    @app_commands.command(name='leave', description='Leave the queue')
    async def leave(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id not in self.queue_data:
            await interaction.response.send_message('You are not in the queue!', ephemeral=True)
            return
            
        del self.queue_data[user_id]
        utils.save_queue_data(self.queue_data)
        
        queue_channel = interaction.guild.get_channel(config.QUEUE_CHANNEL)  
        await queue_channel.send(f'{interaction.user.mention} has left the queue!')
        await interaction.response.send_message('You have been removed from the queue!', ephemeral=True)
        
    @app_commands.command(name='queue', description='Show the current queue')
    async def show_queue(self, interaction: discord.Interaction):
        if not self.queue_data:
            await interaction.response.send_message('The queue is currently empty!')
            return
            
        embed = discord.Embed(title='Current Queue', color=discord.Color.blue())
        for position, user_data in enumerate(self.queue_data.values(), start=1):
            embed.add_field(name=f'#{position}', value=f'<@{user_data["user_id"]}> - {user_data["name"]}', inline=False)
        await interaction.response.send_message(embed=embed)
        
    @app_commands.command(name='next', description='Help the next person in the queue')  
    @app_commands.checks.has_role(config.TA_ROLE)
    async def next(self, interaction: discord.Interaction):
        if not self.queue_data:
            await interaction.response.send_message('The queue is currently empty!')
            return
        
        user_id, user_data = next(iter(self.queue_data.items()))
        
        user_data['helped_by'] = interaction.user.display_name
        user_data['help_start_time'] = datetime.now().isoformat()
        utils.save_queue_data(self.queue_data)
        
        member = interaction.guild.get_member(int(user_id))
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        help_channel = await interaction.guild.create_text_channel(f'help-{member.display_name}', overwrites=overwrites)
        
        await help_channel.send(f'{member.mention} - {interaction.user.mention} is here to help you!')
        await interaction.response.send_message(f'You are now helping {member.mention} in {help_channel.mention}')
        
    @app_commands.command(name='done', description='Finish helping the current student') 
    @app_commands.checks.has_role(config.TA_ROLE)
    async def done(self, interaction: discord.Interaction):
        user_id = next((user_id for user_id, user_data in self.queue_data.items() if user_data['helped_by'] == interaction.user.display_name), None)
        
        if user_id is None:
            await interaction.response.send_message('You are not currently helping anyone!', ephemeral=True)
            return
            
        user_data = self.queue_data[user_id]
        user_data['help_end_time'] = datetime.now().isoformat()
        utils.save_queue_data(self.queue_data)
        
        del self.queue_data[user_id]
        utils.save_queue_data(self.queue_data)
        
        help_channel = interaction.channel
        await help_channel.send(f'{interaction.user.mention} has finished helping <@{user_id}>!')
        await interaction.response.send_message(f'You have finished helping <@{user_id}>!', ephemeral=True)
        await help_channel.delete()
        
    @app_commands.command(name='status', description='Check your position and wait time in the queue')
    async def status(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        if user_id not in self.queue_data:
            await interaction.response.send_message('You are not in the queue!', ephemeral=True)
            return
            
        position = list(self.queue_data.keys()).index(user_id) + 1
        wait_time = datetime.now() - datetime.fromisoformat(self.queue_data[user_id]['join_time'])
        
        await interaction.response.send_message(f'You are currently at position {position} in the queue. You have been waiting for {wait_time}.')
        
    @app_commands.command(name='history', description='Check your help history')
    async def history(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        
        embed = discord.Embed(title=f'Help History for {interaction.user.display_name}', color=discord.Color.green())
        for user_data in self.queue_data.values():
            if user_data['user_id'] == user_id and user_data['help_start_time'] is not None:
                start_time = datetime.fromisoformat(user_data['help_start_time'])
                end_time = datetime.fromisoformat(user_data['help_end_time']) if user_data['help_end_time'] else datetime.now()
                duration = end_time - start_time
                embed.add_field(name=f"Helped by {user_data['helped_by']}", value=f"Start: {start_time}\nDuration: {duration}", inline=False)
                
        if not embed.fields:
            await interaction.response.send_message('You have not received any help yet!')
        else:  
            await interaction.response.send_message(embed=embed)
            
    @tasks.loop(seconds=5.0)
    async def check_queue_timeout(self):
        now = datetime.now()
        to_remove = []
        for user_id, user_data in self.queue_data.items():
            if user_data['help_start_time'] is None and now - datetime.fromisoformat(user_data['join_time']) > timedelta(seconds=config.QUEUE_TIMEOUT):
                to_remove.append(user_id)
                
        for user_id in to_remove:
            del self.queue_data[user_id]
            
        if to_remove:
            utils.save_queue_data(self.queue_data)
            queue_channel = self.bot.get_channel(config.QUEUE_CHANNEL)
            await queue_channel.send(f'{len(to_remove)} user(s) have been removed from the queue due to inactivity.')
            
    @app_commands.command(name='pause', description='Pause the queue')
    @app_commands.checks.has_role(config.TA_ROLE)
    async def pause(self, interaction: discord.Interaction):
        if not self.check_queue_timeout.is_running():
            await interaction.response.send_message('The queue is already paused!', ephemeral=True)
            return
        
        self.check_queue_timeout.cancel()
        await interaction.response.send_message('The queue has been paused.')
        
    @app_commands.command(name='resume', description='Resume the queue')
    @app_commands.checks.has_role(config.TA_ROLE)
    async def resume(self, interaction: discord.Interaction):
        if self.check_queue_timeout.is_running():
            await interaction.response.send_message('The queue is not paused!', ephemeral=True)
            return
        
        self.check_queue_timeout.start()
        await interaction.response.send_message('The queue has been resumed.')

async def setup(bot):
    await bot.add_cog(Queue(bot))
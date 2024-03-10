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
        self.ta_availability = {}
        self.check_queue_timeout.start()
        self.check_session_inactivity.start() 
    
    @app_commands.command(name='help', description='Show available commands')
    async def help(self, interaction: discord.Interaction):
        help_text = '''
        - Students can use the `/join` command to join the queue and provide their contact information
        - Students can use the `/leave` command to leave the queue
        - Students can use the `/status` command to check their position and wait time in the queue
        - Students can use the `/history` command to view their help history
        - Students can use the `/feedback` command to submit feedback for their help session
        - TAs can use the `/queue` command to view the current queue
        - TAs can use the `/next` command to help the next student in the queue (a private text channel and voice channel will be created)
        - TAs can use the `/done` command to finish helping the current student and close the private channels
        - Students can use the `/feedback` command to submit feedback for their help session
        - TAs can use the `/availability` command to set their availability status
        - Admins can use the `/stats` command to view queue statistics
        '''
        await interaction.response.send_message(help_text, ephemeral=True)
            
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
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False, connect=False),
            member: discord.PermissionOverwrite(read_messages=True, connect=True, use_video=True, stream=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True, connect=True, use_video=True, stream=True)
        }
        help_text_channel = await interaction.guild.create_text_channel(f'help-{member.display_name}', overwrites=overwrites)
        help_voice_channel = await interaction.guild.create_voice_channel(f'Help Voice - {member.display_name}', overwrites=overwrites)
        
        self.ta_availability[interaction.user.id] = False
        await help_text_channel.send(f'{member.mention} - {interaction.user.mention} is here to help you in {help_voice_channel.mention}! ')
        await interaction.response.send_message(f'You are now helping {member.mention} in {help_text_channel.mention} and {help_voice_channel.mention}')
        
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
        
        help_text_channel = interaction.channel
        help_voice_channel = discord.utils.get(interaction.guild.voice_channels, name=f'Help Voice - {interaction.user.display_name}')
        
        self.ta_availability[interaction.user.id] = True
        await help_text_channel.send(f'{interaction.user.mention} has finished helping <@{user_id}>!')
        await interaction.response.send_message(f'You have finished helping <@{user_id}>!', ephemeral=True)
        
        await help_text_channel.delete()
        await help_voice_channel.delete()
    
    @app_commands.command(name='feedback', description='Submit feedback for your help session')
    async def feedback(self, interaction: discord.Interaction, rating: int, comment: str):
        user_id = str(interaction.user.id)
        feedback_data = {
            'user_id': user_id,
            'rating': rating,
            'comment': comment,
            'timestamp': datetime.now().isoformat()
        }
        utils.save_feedback(feedback_data)
        await interaction.response.send_message('Thank you for your feedback!', ephemeral=True)
        
    @app_commands.command(name='stats', description='Display queue statistics')
    @app_commands.checks.has_role(config.ADMIN_ROLE)
    async def stats(self, interaction: discord.Interaction):
        total_helped = len([user for user in self.queue_data.values() if user['help_start_time'] is not None])
        await interaction.response.send_message(f'Total students helped: {total_helped}')
        
    @app_commands.command(name='availability', description='Set your availability status')
    @app_commands.checks.has_role(config.TA_ROLE)
    async def availability(self, interaction: discord.Interaction, status: bool):
        self.ta_availability[interaction.user.id] = status
        await interaction.response.send_message(f'Your availability has been set to {"available" if status else "unavailable"}')
    
    @tasks.loop(seconds=60.0)
    async def check_session_inactivity(self):
        inactive_time = timedelta(minutes=config.INACTIVE_SESSION_MINUTES)
        for user_data in self.queue_data.values():
            if user_data['help_start_time'] is not None:
                help_start_time = datetime.fromisoformat(user_data['help_start_time'])
                if datetime.now() - help_start_time > inactive_time:
                    student = self.bot.get_user(int(user_data['user_id']))
                    ta = self.bot.get_user(int(user_data['helped_by']))
                    await self.notify_inactive_session(student, ta)
        
    async def notify_inactive_session(self, student: discord.Member, ta: discord.Member):
        queue_channel = self.bot.get_channel(config.QUEUE_CHANNEL)
        await queue_channel.send(f'{student.mention} {ta.mention} - Your help session has been inactive for a while. Please let us know if you still need assistance.')
        
    async def request_feedback(self, student: discord.Member):
        await student.send('Thanks for attending the help session. Please provide your feedback using the `/feedback` command.')

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
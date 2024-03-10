# discord-office-hours-bot
Generated by Claude 3 Opus

This is a Discord bot that manages an office hours queue for students to request help from teaching assistants (TAs). The bot provides a seamless and efficient way to handle the queue and facilitate communication between students and TAs.

## Features

- Students can join the queue by providing their contact information
- TAs can view the current queue and help the next student in line
- Private text channels are automatically created for one-on-one help sessions between students and TAs
- Students can check their position and wait time in the queue
- Students can view their help history
- TAs can pause and resume the queue as needed
- Inactive students are automatically removed from the queue after a specified timeout period

## Setup

1. Clone the repository:
2. Install the required dependencies in requirements.txt with:
```pip install -r requirements.txt```
3. Create a new Discord bot:
- Go to the Discord Developer Portal: https://discord.com/developers/applications
- Click on "New Application" and give your bot a name
- Navigate to the "Bot" section and click on "Add Bot"
- Copy the bot token (you will need this in step 5)
4. Set up the required roles and channels on your Discord server:
- Create a role for TAs (e.g., "TA") and assign it to the users who will be managing the queue
- Create a role for Admins (e.g., "Admin") and assign it to the users who will have administrative privileges
- Create a text channel for the queue (e.g., "queue")
5. Add a `.env` following `.env.example`, and replace `your_discord_bot_token_here` with your actual bot token.
6. Configure the bot settings in `config.py`:
- Set `ADMIN_ROLE` to the name of the Admin role created in step 4
- Set `TA_ROLE` to the name of the TA role created in step 4
- Set `QUEUE_CHANNEL` to the name of the queue channel created in step 4
- Adjust `QUEUE_TIMEOUT` if needed (default is 300 seconds)
7. Run the bot with:
```python bot.py```

## Usage

## Usage

- Students can use the `/join` command to join the queue and provide their contact information.
- Students can use the `/leave` command to leave the queue.
- Students can use the `/status` command to check their position and wait time in the queue.
- Students can use the `/history` command to view their help history.
- TAs can use the `/queue` command to view the current queue.
- TAs can use the `/next` command to help the next student in the queue. A private text channel will be created for the help session.
- TAs can use the `/done` command to finish helping the current student and close the private text channel.
- TAs can use the `/pause` command to pause the queue and prevent students from joining.
- TAs can use the `/resume` command to resume the queue and allow students to join again.
- Admins can use the `/reload` command to reload all bot extensions without restarting the bot.

## Data Storage

The bot stores queue data in a JSON file located at `data/queue_data.json`. This file is automatically created if it doesn't exist. The queue data is loaded when the bot starts and saved whenever changes occur, such as when a student joins or leaves the queue, or when a TA starts or finishes helping a student. This data is automatically managed by the bot. You don't need to manually edit this file.

The queue data is structured as follows:
```json
{
 "user_id": {
     "user_id": "user_id",
     "name": "user_name",
     "contact_info": "user_contact_info",
     "join_time": "join_time_iso_format",
     "helped_by": "ta_name",
     "help_start_time": "help_start_time_iso_format",
     "help_end_time": "help_end_time_iso_format"
 },
 ...
}
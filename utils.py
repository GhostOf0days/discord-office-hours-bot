import os
import json

async def load_cogs(bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

def load_queue_data():
    if not os.path.exists('data/queue_data.json'):
        return {}
        
    with open('data/queue_data.json', 'r') as file:
        return json.load(file)
        
def save_queue_data(data):
    with open('data/queue_data.json', 'w') as file:
        json.dump(data, file, indent=4)
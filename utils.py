import os
import json

async def load_cogs(bot):
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py') and filename != '__init__.py':
            await bot.load_extension(f'cogs.{filename[:-3]}')

def load_queue_data():
    if not os.path.exists('data/queue_data.json'):
        return {}
        
    with open('data/queue_data.json', 'r') as file:
        return json.load(file)
        
def save_queue_data(data):
    with open('data/queue_data.json', 'w') as file:
        json.dump(data, file, indent=4)

def save_feedback(feedback_data):
    feedback_file = 'data/feedback.json'
    if not os.path.exists(feedback_file):
        with open(feedback_file, 'w') as file:
            json.dump([], file)
            
    with open(feedback_file, 'r') as file:
        feedback_list = json.load(file)
        
    feedback_list.append(feedback_data)
    
    with open(feedback_file, 'w') as file:
        json.dump(feedback_list, file, indent=4)
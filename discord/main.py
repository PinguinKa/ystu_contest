import discord
import credits
from discord.ext import tasks
from discord.ext import commands
import requests

token = credits.bot_token
client = discord.Client()
orders = 0

@tasks.loop(seconds=5) # Повторяется каждые 5 секунд
async def my_loop(channel):
    global orders
    result = '.............................................................\n'
    data = requests.get('http://localhost:5000/api/orders').json()
    if len(data) > orders:
        orders += 1
        result += f'Заказ №{orders}\n'
        result += '.............................................................\n'
        for key in data[-1]:
            result += f'{key}: {data[-1][key]}\n'
        
        await channel.send(result)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    # Мы передаем в функцию myLoop канал, чтобы иметь возможность отправлять сообщения
    if message.content == '$start':
        my_loop.start(message.channel)

client.run(token)
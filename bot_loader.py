# bot_loader.py
import discord
from discord.ext.commands import Bot


class MyBot(Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        intents.guilds = True
        super().__init__(intents=intents)


bot = MyBot()

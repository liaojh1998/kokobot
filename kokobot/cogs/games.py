import random as rng

import discord

logger = logging.getLogger('discord.kokobot.util')


class Games(commands.Cog):
    """Games
    """
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return 'kokobot.cogs.Games'
    
    @commands.command()
    async def slots(self, ctx):
        """ -- Play slots
        Usage: $slots

        React to reroll the slot machine
        """


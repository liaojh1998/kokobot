import asyncio
import logging
import random as rng

import discord
from discord.ext import commands

logger = logging.getLogger('discord.kokobot.random')
emoji_bank = {
    #':left_arrow:': '\U00002B05',
    #':right_arrow:': '\U000027A1',
}


class Random(commands.Cog):
    def __init__(self, bot):
        # config
        self.config = {
            'max_groups': 5,
        }

        self.bot = bot
        rng.seed()
        self.messages = {}
        #self.bot.add_listener(self.react, 'on_reaction_add')

    @commands.group()
    async def random(self, ctx):
        """ -- Random the RNG
        Use $help random <command> for more information.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('Use `$help random` for more information')

    @random.command()
    async def mixer(self, ctx, groups=2):
        """ -- Randomize into groups
        Usage: $random mixer [groups]
        Example: $random mixer 3

        By default, mix into 2 groups.
        """
        title = f"Random Mixer for {groups} Groups"
        r = rng.randint(0, 255)
        b = rng.randint(0, 255)
        g = rng.randint(0, 255)
        colour = r*(16**4) + b*(16**2) + g
        desc = "List of people:\n"
        embed = discord.Embed(title=title, description=desc, colour=colour)
        embed.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        embed.set_footer(text=f"React below to join")
        await ctx.send(embed=embed)

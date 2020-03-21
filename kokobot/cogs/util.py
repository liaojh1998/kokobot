import datetime
import logging

from discord.ext import commands

logger = logging.getLogger('discord.kokobot.util')


class Util(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return 'kokobot.cogs.Util'

    @commands.command()
    async def ping(self, ctx):
        if ctx.prefix != '$':
            return

        start = ctx.message.created_at.timestamp()
        end = datetime.datetime.utcnow().timestamp()
        await ctx.send('`{} ms`'.format(int(end - start)))

import logging
import sqlite3

from discord.ext import commands

logger = logging.getLogger('discord.kokobot.koko')


class Koko(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return 'kokobot.cogs.Koko'

    @commands.group()
    async def koko(self, ctx):
        """ -- Koko the notetaker
        Use `$help koko <command>` for more information.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('Use $help koko for more information')

    @koko.command()
    async def add(self, ctx):
        """ -- Add a note for a name
        Usage: $koko add <name> <note>
        Example: $koko add hello world

        Then, input `*hello` to get back your note \"world\".
        """
        await ctx.send('Coming soon')

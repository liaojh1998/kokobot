import datetime
import logging

from discord.ext import commands

logger = logging.getLogger('discord.kokobot.util')


class Util(commands.Cog):
    """Utility commands
    """
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return 'kokobot.cogs.Util'

    @commands.command()
    async def ping(self, ctx):
        """ -- Ping Kokobot
        Usage: $ping
        """
        if ctx.prefix != '$':
            return

        recv_start = ctx.message.created_at.timestamp()
        recv_end = datetime.datetime.utcnow().timestamp()
        send_start = datetime.datetime.utcnow().timestamp()
        message = await ctx.send('.')
        send_end = datetime.datetime.utcnow().timestamp()
        await message.edit(content='Recieve: `{} ms`\nSend: `{} ms`'.format(int((recv_end - recv_start) * 1000), int((send_end - send_start) * 1000)))

    @commands.command()
    async def shutdown(self, ctx):
        """ -- Shutdown Kokobot
        Usage: $shutdown
        Only members of 'admin uwu', 'Officers', and 'bot boi' may use this.
        """
        # admins
        admin_role = ['bot boi', 'admin uwu', 'Officers']

        can_shutdown = await ctx.bot.is_owner(ctx.message.author)
        if not can_shutdown:
            for role in ctx.channel.guild.roles:
                if role.name in admin_role:
                    if ctx.message.author in role.members:
                        can_shutdown = True
                        break;
        # Shutdown
        if can_shutdown:
            sent = await ctx.send('Shutting down bot...')
            logger.info('Shutting down as {}'.format(ctx.message.author))
            await ctx.bot.logout()
        else:
            sent = await ctx.send('Cannot shutdown as {}'.format(ctx.message.author))
            await ctx.message.delete(delay=5)
            await sent.delete(delay=5)

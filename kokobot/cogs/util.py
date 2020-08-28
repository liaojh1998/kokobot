import datetime
import logging
import typing

import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
from discord.errors import Forbidden

logger = logging.getLogger('discord.kokobot.util')


class Util(commands.Cog):
    """Utility commands
    """
    def __init__(self, bot):
        self.bot = bot

    def __str__(self):
        return 'kokobot.cogs.Util'

    @commands.command()
    async def nick(self, ctx, *, nickname: str=""):
        """ -- Change your nickname
        Usage: $nick [nickname]
        Example: $nick hello
        Special case: $nick, which removes your nickname

        As default, typing $nick will simply remove your nickname.
        """
        if len(nickname) > 32:
            await ctx.send("Nickname must be 32 or fewer characters.")
            return
        user = ctx.message.author
        old_name = user.display_name
        if len(nickname) == 0:
            nickname = None
        await user.edit(nick=nickname, reason="[{}] {} requested change nick to {}".format(datetime.datetime.utcnow().timestamp(), old_name, nickname))
        logger.info("Changed nickname of {} to {}.".format(old_name, user.display_name))
        await ctx.send("Changed your nickname to {}, {}.".format(user.display_name, user.mention))

    @nick.error
    async def nick_error(self, ctx, error):
        if isinstance(error.original, Forbidden):
            await ctx.send("Cannot change nickname for you, {}. Bot permissions hierarchy is lower than your roles or you're the owner.".format(ctx.message.author.mention))
        else:
            logger.info("Setting nickname encountered an error: {}".format(error))
            await ctx.send("Bot error!")

    @commands.command()
    async def ping(self, ctx):
        """ -- Ping Kokobot
        Usage: $ping
        """
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
                        break
        # Shutdown
        if can_shutdown:
            sent = await ctx.send('Shutting down bot...')
            logger.info('Shutting down as {}'.format(ctx.message.author))
            await ctx.bot.logout()
        else:
            sent = await ctx.send('Cannot shutdown as {}'.format(ctx.message.author))
            await ctx.message.delete(delay=5)
            await sent.delete(delay=5)

    @commands.command()
    async def ava(self, ctx):
        """ -- Get Avatar Image
        Usage: $ava [user]

        If no user, then get avatar of the message's author
        """

        mentions = ctx.message.mentions

        if len(mentions) == 0:
            member = ctx.message.author
        else:
            member = mentions.pop(0)

        name = str(member)
        avatar_url = str(member.avatar_url)

        embed = discord.Embed(colour=2818026) # Aqua
        embed.set_author(name=name, icon_url=avatar_url)
        embed.set_image(url=avatar_url)
        sent = await ctx.send(embed=embed)

    @commands.command()
    async def purge(self, ctx, count):
        """ -- Purge past messages
        Usage: $purge <count>

        Delete the past `count` amount of messages in
        the channel, excluding the command message. However,
        the command message will be deleted as well.
        """

        channel = ctx.channel
        channel.purge(limit=count+1)  # Including the purge command
        sent = await ctx.send(f'{ctx.author} purged {count} messages.')

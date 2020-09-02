import asyncio
import datetime
import logging
import typing

import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument
from discord.errors import Forbidden

logger = logging.getLogger('discord.kokobot.util')
emoji_bank = {
    ':left_arrow:': '\U00002B05',
    ':right_arrow:': '\U000027A1',
}


class Util(commands.Cog):
    """Utility commands
    """
    def __init__(self, bot):
        self.messages = {}
        self.bot = bot
        self.bot.add_listener(self.on_ready, 'on_ready')
        self.bot.add_listener(self.react, 'on_reaction_add')

    def __str__(self):
        return 'kokobot.cogs.Util'

    async def on_ready(self):
        self.owner = self.bot.get_user(self.bot.owner_id)

    async def react(self, reaction, user):
        if (user == self.bot.user
                or not reaction.emoji in (emoji_bank[':left_arrow:'], emoji_bank[':right_arrow:'])
                or not reaction.message.id in self.messages):
            return

        # Get new page number
        message_id = reaction.message_id
        page = self.messages[message_id]['page']
        if reaction.emoji == emoji_bank[':left_arrow:']:
            page -= 1
            if page < 0:
                page = 0
        if reaction.emoji == emoji_bank[':right_arrow:']:
            page += 1

        # Reset message
        await self.list_users(self.messages[message_id]['message'],
                              self.messages[message_id]['user']
                              page,
                              self.messages[message_id]['members'])

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
    async def purge(self, ctx, count: int):
        """ -- Purge past messages
        Usage: $purge <count>

        Delete the past `count` amount of messages in
        the channel, excluding the command message. However,
        the command message will be deleted as well.
        """
        # admins
        admin_role = ['bot boi', 'admin uwu', 'Officers']

        # Check for permission to purge
        author = ctx.message.author
        can_purge = await ctx.bot.is_owner(author)
        if not can_purge:
            for role in ctx.channel.guild.roles:
                if role.name in admin_role:
                    if ctx.message.author in role.members:
                        can_purge = True

        # Purge
        await ctx.message.delete()  # Delete the purge command first
        if not can_purge:
            await ctx.send(f'{author.mention} do not have permissions to purge.')
            return
        if count > 100:  # Limit purge count
            await ctx.send(f'{author.mention}, you can only purge up to 100 messages at a time.')
            return
        messages = await ctx.channel.purge(limit=count)
        sent = await ctx.send(f'Purged {len(messages)} of the {count} messages requested by {author.mention}.')
        logger.info(f'Purged {len(messages)} of the {count} messages requested by {author}')

    @commands.command()
    async def users(self, ctx):
        """ -- List all users and their join date.

        Prints all users and their join date, sorted by date they joined.
        This command fails if there are more than 500 users.
        """

        try:
            message = await ctx.send('Listing users...')
            guild = ctx.guild
            members = await guild.fetch_members(limit=500).flatten()
            sorted(members, key=lambda member: member.joined_at)
            await self.list_users(message, ctx.author, 0, members)
        except Exception as e:
            logger.info('Python error: {}'.format(e))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))

    async def clear_message(self, future, message):
        await asyncio.sleep(60)
        if not future.cancelled():
            # FIXME: clear reactions for DMs are unattainable because
            # 'manage_messages' permission cannot be attained for all DMs
            await message.clear_reactions()
            self.messages.pop(message.id)

    async def list_users(self, message, user, page, members)
        # Cleanup of previous message
        if message.id in self.messages:
            self.messages[message.id]['future'].cancel()
        # FIXME: clear reactions for DMs are unattainable because
        # 'manage_messages' permission cannot be attained for all DMs
        await message.clear_reactions()

        MEMBERS = 10  # members to display per page
        pages = len(members) / MEMBERS
        if len(members) % MEMBERS > 0:
            pages += 1
        # make sure page is within limit
        if page < 0:
            page = 0
        if page > pages - 1:
            page = pages - 1

        try:
            title = "List of users and their join date, as requested by {}".format(user)
            req = members[page*MEMBERS:(page+1)*MEMBERS]
            desc = None
            if len(req) > 0:
                desc = ""
                for i in range(len(req)):
                    m = req[i]
                    timestr = ": UNKNOWN"
                    if not m.joined_at is None:
                        timestr = ": " + m.joined_at.strftime("%m-%d-%Y")
                    desc += f"{pa%m/%d/%Yge*10 + i + 1}. {m.nick} ({m})" + timestr + "\n"
            embed = discord.Embed(title=title, description=desc, colour=65280)  # Green
            actual_page = page + 1
            if pages == 0:
                actual_page = 0
            embed.set_footer(text=f"Page {actual_page} of {pages}")

            # Edit the message
            await message.edit(content=None, embed=embed)
            logger.info('Sent users page {} of {} for "{}"'.format(actual_page, pages, user))

            # React to the message
            has_more = False
            if actual_page > 1:
                has_more = True
                await message.add_reaction(emoji_bank[':left_arrow:'])
            if actual_page < pages:
                has_more = True
                await message.add_reaction(emoji_bank[':right_arrow:'])

            if has_more:
                # Add message to messages dict
                self.messages[message.id] = {}
                self.messages[message.id]['message'] = message
                self.messages[message.id]['user'] = user
                self.messages[message.id]['page'] = page
                self.messages[message.id]['members'] = members

                # Schedule a future clear of message
                future = asyncio.Future()
                asyncio.ensure_future(self.clear_message(future, message))
                self.messages[message.id]['future'] = future
        except Exception as e:
            logger.info('Python error: {}'.format(e))
            await message.channel.send('Bot error, {} pls fix!'.format(self.owner.mention))

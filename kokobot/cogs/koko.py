import asyncio
import logging
import math
import sqlite3
import typing

import discord
from discord.ext import commands
from discord.ext.commands.errors import MissingRequiredArgument

logger = logging.getLogger('discord.kokobot.koko')
emoji_bank = {
    ':left_arrow:': '\U00002B05',
    ':right_arrow:': '\U000027A1',
}


class Koko(commands.Cog):
    def __init__(self, bot):
        # config
        self.config = {
            'table_name': 'koko',
            'schema': '''(
                date INT UNIQUE,
                user INT,
                name TEXT UNIQUE,
                value TEXT
            )''',
            'per_page': 10,
        }

        self.bot = bot
        self.bot.add_listener(self.on_ready, 'on_ready')
        self.bot.add_listener(self.setup, 'on_connect')
        self.bot.add_listener(self.setup, 'on_resume')
        self.bot.add_listener(self.teardown, 'on_disconnect')
        self.bot.add_listener(self.get, 'on_message')
        self.messages = {}
        self.bot.add_listener(self.react, 'on_reaction_add')

    def __str__(self):
        return 'kokobot.cogs.Koko'

    async def setup(self):
        logger.info("Beginning connection to sqlite...")
        self.conn = sqlite3.connect('kokobot.db')

        # Create table if it doesn't exist
        c = self.conn.cursor()
        c.execute(f'''SELECT name FROM sqlite_master WHERE type="table" AND name="{self.config['table_name']}"''')
        has = c.fetchone()
        if has is None:
            logger.info(f'Created table "{self.config["table_name"]}"')
            c.execute(f'''CREATE TABLE {self.config['table_name']} {self.config['schema']}''')
        else:
            logger.info(f'Found table "{self.config["table_name"]}"')
        self.conn.commit()

    async def teardown(self):
        logger.info("Closing connection to sqlite...")
        self.conn.close()

    async def on_ready(self):
        self.owner = self.bot.get_user(self.bot.owner_id)

    @commands.group()
    async def koko(self, ctx):
        """ -- Koko the notetaker
        Associates a name with a note. Can be a name for memes, links, and anything.
        Use $help koko <command> for more information.
        """
        if ctx.invoked_subcommand is None:
            await ctx.send('Use `$help koko` for more information')

    @koko.command()
    async def add(self, ctx, name, *, note):
        """ -- Add a note for a name
        Usage: $koko add <name> <note>
        Example: $koko add hello world

        Then, input *hello to get back \"world\".
        """
        date = ctx.message.created_at.timestamp()
        user = ctx.message.author.id
        try:
            c = self.conn.cursor()
            c.execute(f'INSERT INTO {self.config["table_name"]} VALUES (?, ?, ?, ?)',
                      (date, user, name, note))
            self.conn.commit()
            logger.info('Added note `{}` for {}'.format(name, ctx.message.author))
            await ctx.send("Added `*{}` with note: {}".format(name, note))
        except sqlite3.IntegrityError as e:
            logger.info('Adding note `{}` for {} raised database error: {}'.format(name, ctx.message.author, e))
            await ctx.send('`*{}` already exist.'.format(name))

    @add.error
    async def add_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send('Invalid arguments for `$koko add`, use `$help koko add` for more information.')
        elif isinstance(error.original, sqlite3.Error):
            logger.info('Database error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))
        elif isinstance(error, Exception):
            logger.info('Python error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))

    async def get(self, message):
        """ -- Get an added note.
        Usage: *name

        You can add multiple in one message by adding each in a different line.
        """
        if message.author != self.bot.user and message.author.bot:
            return

        lines = message.content.split('\n')
        for line in lines:
            if len(line) > 0 and line[0] == '*':
                if message.author == self.bot.user:
                    await message.channel.send('Cannot chain notes from Kokobot, sorry buddy!')
                    return

                name = line[1:]
                if len(name) == 0:
                    sent = await message.channel.send('Empty name.')
                    await sent.delete(delay=5)
                    await message.delete(delay=5)
                    return

                try:
                    c = self.conn.cursor()
                    c.execute(f'SELECT value FROM {self.config["table_name"]} WHERE name=(?) LIMIT 1', (name,))
                    note = c.fetchone()
                    self.conn.commit()
                    if note is None:
                        await message.channel.send('`*{}` does not exist.'.format(name))
                    else:
                        value = note[0]
                        await message.channel.send(value)
                except sqlite3.Error as e:
                    logger.info('Database error: {}'.format(e))
                    await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))
                except Exception as e:
                    logger.info('Python error: {}'.format(e))
                    await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))

    @koko.command()
    async def remove(self, ctx, *, name):
        """ -- Remove/Delete a note associated with a name
        Usage: $koko remove/delete <name>
        Example: $koko remove/delete hello
        """
        deleter = ctx.message.author.id
        c = self.conn.cursor()
        c.execute(f'SELECT user FROM {self.config["table_name"]} WHERE name=(?) LIMIT 1', (name,))
        user = c.fetchone()
        if user is None:
            await ctx.send('`*{}` does not exist.'.format(name))
        else:
            owner = user[0]
            if owner != deleter:
                owner = ctx.bot.get_user(owner)
                await ctx.send('`*{}` belongs to {}.\nCannot delete a note that\'s not your\'s, {}.'.format(name, owner, ctx.message.author.mention))
            else:
                c.execute(f'DELETE FROM {self.config["table_name"]} WHERE name=(?)', (name,))
                logger.info('Removed note `{}` for {}'.format(name, ctx.message.author))
                await ctx.send("Removed `*{}`.".format(name))
        self.conn.commit()

    @remove.error
    async def remove_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send('Invalid arguments for `$koko remove/delete`, use `$help koko remove/delete` for more information.')
        elif isinstance(error, sqlite3.Error):
            logger.info('Database error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))
        elif isinstance(error, Exception):
            logger.info('Python error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))

    @koko.command()
    async def delete(self, ctx, *, name):
        """ -- Remove/Delete a note associated with a name
        Usage: $koko remove/delete <name>
        Example: $koko remove/delete hello
        """
        await self.remove(ctx=ctx, name=name)

    @delete.error
    async def delete_error(self, ctx, error):
        await self.remove_error(ctx, error)

    async def clear_message(self, future, message):
        await asyncio.sleep(60)
        if not future.cancelled():
            await message.clear_reactions()
            self.messages.pop(message.id)

    async def react(self, reaction, user):
        if (user == self.bot.user
                or not reaction.emoji in (emoji_bank[':left_arrow:'], emoji_bank[':right_arrow:'])
                or not reaction.message.id in self.messages):
            return

        # Get new page number
        message_id = reaction.message.id
        page = self.messages[message_id]['page']
        if reaction.emoji == emoji_bank[':left_arrow:']:
            page -= 1
            if page < 0:
                page = 0
        if reaction.emoji == emoji_bank[':right_arrow:']:
            page += 1

        # Reset message
        if self.messages[message_id]['type'] == 'list':
            await self.list_notes(self.messages[message_id]['message'], page,
                                  self.messages[message_id]['user'])
        elif self.messages[message_id]['type'] == 'search':
            await self.search_notes(self.messages[message_id]['message'], page,
                                    self.messages[message_id]['query'])

    @koko.command()
    async def who(self, ctx, *, name):
        """ -- Check who has made the note with <name>
        Uasge: $koko who <name>
        Example: $koko who hello
        """
        c = self.conn.cursor()
        c.execute(f'SELECT user FROM {self.config["table_name"]} WHERE name=(?)', (name,))
        user = c.fetchone()
        self.conn.commit()
        if user is None:
            await ctx.send("`*{}` does not exist.".format(name))
        else:
            user = self.bot.get_user(user[0])
            await ctx.send("`*{}` was added by {}.".format(name, user))

    @who.error
    async def who_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send('Invalid arguments for `$koko who`, use `$help koko who` for more information.')
        elif isinstance(error.original, sqlite3.Error):
            logger.info('Database error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))
        elif isinstance(error, Exception):
            logger.info('Python error: {}'.format(error))
            await ctx.send('Bot error, {} pls fix!'.format(self.owner.mention))

    @koko.command()
    async def list(self, ctx, user: discord.User=None):
        """ -- List a set of notes (belonging to a user)
        Usage: $koko list [user]
        Example: $koko list @Jay#5035

        If user field is empty, then list all notes.
        If user field is not empty, it needs to tag the user.
        """
        message = await ctx.send('Listing...')
        await self.list_notes(message, 0, user)

    async def list_notes(self, message, page, user):
        # Cleanup of previous message
        if message.id in self.messages:
            self.messages[message.id]['future'].cancel()
        await message.clear_reactions()

        try:
            # Count
            c = self.conn.cursor()
            if user is None:
                c.execute(f'SELECT COUNT(*) FROM {self.config["table_name"]}')
            else:
                c.execute(f'SELECT COUNT(*) FROM {self.config["table_name"]} WHERE user=(?)', (user.id,))
            count = c.fetchone()[0]
            count = math.ceil(count / self.config['per_page'])
            if page > count - 1:
                page = count - 1

            # Fetch Results
            if count > 0:
                if user is None:
                    c.execute(f'SELECT name FROM {self.config["table_name"]} ORDER BY name LIMIT {self.config["per_page"]} OFFSET {page * self.config["per_page"]}')
                else:
                    c.execute(f'SELECT name FROM {self.config["table_name"]} WHERE user=(?) ORDER BY name LIMIT {self.config["per_page"]} OFFSET {page * self.config["per_page"]}', (user.id,))
                results = c.fetchall()
            self.conn.commit()

            # Create the Embed
            title = "List Results: Notes of "
            if user is None:
                title += f"@everyone"
            else:
                title += f"{user}"
            desc = None
            if count > 0:
                desc = '\n'.join(['*' + _[0] for _ in results])
            embed = discord.Embed(title=title, description=desc, colour=2818026) # Aqua
            actual_page = page + 1
            if count == 0:
                actual_page = 0
            embed.set_footer(text=f"Page {actual_page} of {count}")

            # Edit the message
            await message.edit(content=None, embed=embed)
            logger.info('Sent koko list page {} of {} for {}'.format(actual_page, count, user))

            # React to the message
            has_more = False
            if actual_page > 1:
                has_more = True
                await message.add_reaction(emoji_bank[':left_arrow:'])
            if actual_page < count:
                has_more = True
                await message.add_reaction(emoji_bank[':right_arrow:'])

            if has_more:
                # Add message to messages dict
                self.messages[message.id] = {}
                self.messages[message.id]['message'] = message
                self.messages[message.id]['type'] = 'list'
                self.messages[message.id]['user'] = user
                self.messages[message.id]['page'] = page

                # Schedule a future clear of message
                future = asyncio.Future()
                asyncio.ensure_future(self.clear_message(future, message))
                self.messages[message.id]['future'] = future
        except sqlite3.Error as e:
            logger.info('Database error: {}'.format(e))
            await message.channel.send('Bot error, {} pls fix!'.format(self.owner.mention))
        except Exception as e:
            logger.info('Python error: {}'.format(e))
            await message.channel.send('Bot error, {} pls fix!'.format(self.owner.mention))

    @koko.command()
    async def search(self, ctx, *, query=""):
        """ -- Search for a set of notes that contains the <query>
        Usage: $koko search <query>
        Example: $koko search hello wow
        """
        query = query.replace('\"', '')
        message = await ctx.send('Searching...')
        await self.search_notes(message, 0, query)

    async def search_notes(self, message, page, query):
        # Cleanup of previous message
        if message.id in self.messages:
            self.messages[message.id]['future'].cancel()
        await message.clear_reactions()

        try:
            # Count
            c = self.conn.cursor()
            c.execute(f'SELECT COUNT(*) FROM {self.config["table_name"]} WHERE name LIKE "%{query}%"')
            count = c.fetchone()[0]
            count = math.ceil(count / self.config['per_page'])
            if page > count - 1:
                page = count - 1

            # Fetch Results
            if count > 0:
                c.execute(f'SELECT name FROM {self.config["table_name"]} WHERE name LIKE "%{query}%" ORDER BY name LIMIT {self.config["per_page"]} OFFSET {page * self.config["per_page"]}')
                results = c.fetchall()
            self.conn.commit()

            # Create the Embed
            title = f"Search Results: Contains \"{query}\""
            desc = None
            if count > 0:
                desc = '\n'.join(['*' + _[0] for _ in results])
            embed = discord.Embed(title=title, description=desc, colour=16761035) # Pink
            actual_page = page + 1
            if count == 0:
                actual_page = 0
            embed.set_footer(text=f"Page {actual_page} of {count}")

            # Edit the message
            await message.edit(content=None, embed=embed)
            logger.info('Sent koko search page {} of {} for "{}"'.format(actual_page, count, query))

            # React to the message
            has_more = False
            if actual_page > 1:
                has_more = True
                await message.add_reaction(emoji_bank[':left_arrow:'])
            if actual_page < count:
                has_more = True
                await message.add_reaction(emoji_bank[':right_arrow:'])

            if has_more:
                # Add message to messages dict
                self.messages[message.id] = {}
                self.messages[message.id]['message'] = message
                self.messages[message.id]['type'] = 'search'
                self.messages[message.id]['query'] = query
                self.messages[message.id]['page'] = page

                # Schedule a future clear of message
                future = asyncio.Future()
                asyncio.ensure_future(self.clear_message(future, message))
                self.messages[message.id]['future'] = future
        except sqlite3.Error as e:
            logger.info('Database error: {}'.format(e))
            await message.channel.send('Bot error, {} pls fix!'.format(self.owner.mention))
        except Exception as e:
            logger.info('Python error: {}'.format(e))
            await message.channel.send('Bot error, {} pls fix!'.format(self.owner.mention))

import asyncio
import logging

import discord
from discord.ext import commands

logger = logging.getLogger('discord.kokobot.roles')
emoji_bank = {
    ':woozy_face:': '\U0001F974',
    ':hatching_chick:': '\U0001F423',
    ':zany_face:': '\U0001F92A',
    ':partying_face:': '\U0001F973',
    ':nerd_face:': '\U0001F913',
    ':sunglasses:': '\U0001F60E',
    ':innocent:': '\U0001F607',

    ':male_sign:': '\U00002642',
    ':female_sign:': '\U00002640',
    ':transgender_symbol:': '\U000026A7',
    ':rainbow_flag:': '\U0001F3F3\uFE0F\u200D\U0001F308',

    ':metal:': '\U0001F918',
    ':star2:': '\U0001F31F',
    ':mortar_board:': '\U0001F393',
}


class Roles(commands.Cog):
    """Modifies the member roles in this server. Check out #\U0001F440-roles channel.

    Commands:
      +number -- Add a role
      -number -- Remove a role"""
    def __init__(self, bot):
        # Config
        self.config = {
            'channel': 'roles',
            'emoji_roles': {
                "Member": emoji_bank[':metal:'],
                "Alumni": emoji_bank[':mortar_board:'],
                "External Being": emoji_bank[':star2:'],
            },
            'year_roles': {
                "Freshman": emoji_bank[':partying_face:'],
                "Sophomore": emoji_bank[':zany_face:'],
                "Junior": emoji_bank[':nerd_face:'],
                "Senior": emoji_bank[':sunglasses:'],
            },
            'gender_roles': {
                "He/Him": emoji_bank[':male_sign:'],
                "She/Her": emoji_bank[':female_sign:'],
                "They/Them": emoji_bank[':transgender_symbol:'],
                "Ask My Gender": emoji_bank[':rainbow_flag:'],
            },
            'invalid_roles': [
                '@everyone', 'kokobot', 'bot boi', 'AI', 'Ascended Admin',
                'Officers', 'Removal', 'MEE6', 'Kulture Korner',
                'OG Server Creator :)', 'Old officers', 'Server Booster',
            ],
        }
        self.config['invalid_roles'].extend(self.config['emoji_roles'])
        self.config['invalid_roles'].extend(self.config['year_roles'])
        self.config['invalid_roles'].extend(self.config['gender_roles'])

        # Role Messages
        emoji_role_message = 'React if you are an:\n'
        year_role_message = 'React if you are a:\n'
        gender_role_message = ('\nUse these roles below to help others on the server to identify you.\n'
                               'Feel free to contact the officers for any questions, comments, or concerns!\n')

        # Initialize
        self.bot = bot
        self.hello_ids = []
        self.emoji_roles_bot = EmojiRoles(bot, self.config, 'emoji_roles', emoji_role_message)
        self.year_roles_bot = EmojiRoles(bot, self.config, 'year_roles', year_role_message)
        self.gender_roles_bot = EmojiRoles(bot, self.config, 'gender_roles', gender_role_message)
        self.text_roles_bot = TextRoles(bot, self.config)
        self.bot.add_cog(self.emoji_roles_bot)
        self.bot.add_cog(self.text_roles_bot)
        self.bot.add_listener(self.on_ready)

    def __str__(self):
        return 'kokobot.cogs.Roles'

    async def on_ready(self):
        # Search channels
        self.channels = []
        for guild in self.bot.guilds:
            for channel in guild.channels:
                if self.config['channel'] in channel.name:
                    logger.info('Found channel: %s #%s' % (guild.name, channel.name))
                    self.channels.append(channel)
                    break

        # Clean channels
        for channel in self.channels:
            await channel.purge(limit=None)
            hello_id = await channel.send('Hello! :smiling_face_with_3_hearts:')
            self.hello_ids.append(hello_id)

        # Ready other role bots
        await self.emoji_roles_bot.on_ready(self.channels)
        await self.year_roles_bot.on_ready(self.channels)
        await self.gender_roles_bot.on_ready(self.channels)
        await self.text_roles_bot.on_ready(self.channels)

        # Clear chat
        await self.clear()

    async def clear(self):
        while True:
            await asyncio.sleep(60 * 60) # every 60 minutes
            message_ids = []
            for hello_id in self.hello_ids:
                if not hello_id is None:
                    message_ids.append(hello_id)
            for channel in self.emoji_roles_bot.channel_info:
                if ('message' in self.emoji_roles_bot.channel_info[channel]
                        and not self.emoji_roles_bot.channel_info[channel]['message'] is None):
                    message_ids.append(self.emoji_roles_bot.channel_info[channel]['message'].id)
            for channel in self.year_roles_bot.channel_info:
                if ('message' in self.year_roles_bot.channel_info[channel]
                        and not self.year_roles_bot.channel_info[channel]['message'] is None):
                    message_ids.append(self.year_roles_bot.channel_info[channel]['message'].id)
            for channel in self.gender_roles_bot.channel_info:
                if ('message' in self.gender_roles_bot.channel_info[channel]
                        and not self.gender_roles_bot.channel_info[channel]['message'] is None):
                    message_ids.append(self.gender_roles_bot.channel_info[channel]['message'].id)
            for channel in self.text_roles_bot.channel_info:
                if ('message' in self.text_roles_bot.channel_info[channel]
                        and not self.text_roles_bot.channel_info[channel]['message'] is None):
                    message_ids.append(self.text_roles_bot.channel_info[channel]['message'].id)
            def is_role_msg(message):
                return not message.id in message_ids
            for channel in self.channels:
                await channel.purge(limit=None, check=is_role_msg)


class EmojiRoles(commands.Cog):
    def __init__(self, bot, config, roles_name, head_message):
        self.bot = bot
        self.config = config
        self.roles_name = roles_name
        self.head_message = head_message
        self.channels = {}
        self.guild_to_channel = {}
        self.channel_info = {}
        self.bot.add_listener(self.add_role, 'on_reaction_add')
        self.bot.add_listener(self.remove_role, 'on_reaction_remove')
        self.bot.add_listener(self.redo_roles_on_create, 'on_guild_role_create')
        self.bot.add_listener(self.redo_roles_on_delete, 'on_guild_role_delete')
        self.bot.add_listener(self.redo_roles_on_update, 'on_guild_role_update')

    async def on_ready(self, channels):
        for channel in channels:
            self.channels[channel.id] = channel
            self.guild_to_channel[channel.guild.id] = channel
            self.channel_info[channel.id] = {}
            await self.setup_roles(channel)

    async def setup_roles(self, channel):
        if 'message' in self.channel_info[channel.id]:
            if not self.channel_info[channel.id]['message'] is None:
                await self.channel_info[channel.id]['message'].delete()
            self.channel_info[channel.id]['message'] = None

        # Setup roles
        self.channel_info[channel.id]['roles'] = {}
        for role in channel.guild.roles:
            for emoji_role, emoji in self.config[self.roles_name].items():
                if emoji_role in role.name:
                    self.channel_info[channel.id]['roles'][emoji] = role
                    break

        if self.channel_info[channel.id]['roles']:
            # Send help string
            help_str = self.head_message
            for emoji_role, emoji in self.config[self.roles_name].items():
                help_str += f'{emoji} {emoji_role}\n'
            self.channel_info[channel.id]['message'] = await channel.send(help_str)

            # React to the message
            for emoji in self.config[self.roles_name].values():
                if emoji in self.channel_info[channel.id]['roles']:
                    await self.channel_info[channel.id]['message'].add_reaction(emoji)

    async def redo_roles_on_create(self, role):
        logger.info('Server created role "{}".'.format(role.name))
        await self.setup_roles(self.guild_to_channel[role.guild.id])

    async def redo_roles_on_delete(self, role):
        logger.info('Server deleted role "{}".'.format(role.name))
        await self.setup_roles(self.guild_to_channel[role.guild.id])

    async def redo_roles_on_update(self, before, after):
        logger.info('Server updated role "{}".'.format(after.name))
        await self.setup_roles(self.guild_to_channel[after.guild.id])

    async def add_role(self, reaction, user):
        if (user == self.bot.user
                or not reaction.message.channel.id in self.channel_info
                or reaction.message.id != self.channel_info[reaction.message.channel.id]['message'].id):
            return

        # Add the family role
        if reaction.emoji in self.channel_info[reaction.message.channel.id]['roles']:
            role = self.channel_info[reaction.message.channel.id]['roles'][reaction.emoji]
            try:
                await user.add_roles(
                    role,
                    reason='kokobot reaction {} from {}'.format(reaction.message.id, user))
                logger.info('Added "{}" role for {}.'.format(role.name, user))
            except discord.errors.Forbidden:
                sent = await reaction.message.channel.send('Not enough permissions to add "{}" role for {}. (Check role hierarchy)'.format(role.name, user))
                await sent.delete(delay=5)

    async def remove_role(self, reaction, user):
        if (user == self.bot.user
                or not reaction.message.channel.id in self.channel_info
                or reaction.message.id != self.channel_info[reaction.message.channel.id]['message'].id):
            return

        # Add the family role
        if reaction.emoji in self.channel_info[reaction.message.channel.id]['roles']:
            role = self.channel_info[reaction.message.channel.id]['roles'][reaction.emoji]
            try:
                await user.remove_roles(
                    role,
                    reason='kokobot reaction {} from {}'.format(reaction.message.id, user))
                logger.info('Removed "{}" role for {}.'.format(role.name, user))
            except discord.errors.Forbidden:
                sent = await reaction.message.channel.send('Not enough permissions to remove "{}" role for {}. (Check role hierarchy)'.format(role.name, user))
                await sent.delete(delay=5)


class TextRoles(commands.Cog):
    def __init__(self, bot, config):
        self.bot = bot
        self.config = config
        self.channels = {}
        self.guild_to_channel = {}
        self.channel_info = {}
        self.bot.add_listener(self.modify_roles, 'on_message')
        self.bot.add_listener(self.redo_roles_on_create, 'on_guild_role_create')
        self.bot.add_listener(self.redo_roles_on_delete, 'on_guild_role_delete')
        self.bot.add_listener(self.redo_roles_on_update, 'on_guild_role_update')

    async def on_ready(self, channels):
        for channel in channels:
            self.channels[channel.id] = channel
            self.guild_to_channel[channel.guild.id] = channel
            self.channel_info[channel.id] = {}
            await self.setup_roles(channel)

    async def setup_roles(self, channel):
        if 'message' in self.channel_info[channel.id]:
            if not self.channel_info[channel.id]['message'] is None:
                await self.channel_info[channel.id]['message'].delete()
            self.channel_info[channel.id]['message'] = None

        # Setup roles
        self.channel_info[channel.id]['roles'] = []
        for role in channel.guild.roles:
            invalid = False
            for invalid_role in self.config['invalid_roles']:
                if invalid_role in role.name:
                    invalid = True
                    break
            if not invalid:
                self.channel_info[channel.id]['roles'].append(role)
        self.channel_info[channel.id]['roles'].reverse()

        if self.channel_info[channel.id]['roles']:
            # Send help string
            help_str = '\nShow your interests and potentially unlock new text channels with these roles:\n'
            for idx, role in enumerate(self.channel_info[channel.id]['roles']):
                help_str += '\t\t`{}`: {}\n'.format(idx, role.name)
            help_str += 'Use `+number` to add or `-number` to remove a role.\n'
            help_str += 'For example, `+0` will give you the role "{}", and `-0` will remove that role for you.'.format(self.channel_info[channel.id]['roles'][0].name)
            self.channel_info[channel.id]['message'] = await channel.send(help_str)

    async def redo_roles_on_create(self, role):
        logger.info('Server created role "{}".'.format(role.name))
        await self.setup_roles(self.guild_to_channel[role.guild.id])

    async def redo_roles_on_delete(self, role):
        logger.info('Server deleted role "{}".'.format(role.name))
        await self.setup_roles(self.guild_to_channel[role.guild.id])

    async def redo_roles_on_update(self, before, after):
        logger.info('Server updated role "{}".'.format(after.name))
        await self.setup_roles(self.guild_to_channel[after.guild.id])

    async def modify_roles(self, message):
        if (message.author == self.bot.user
                or len(message.content) == 0
                or message.content[0] == '$'
                or not message.channel.id in self.channels):
            return

        # Check the command is legitimate
        if not (message.content[0] in ('+', '-')
                and message.content[1:].isdigit()):
            sent = await message.channel.send('Invalid role command.')
            await message.delete(delay=5)
            await sent.delete(delay=5)
            return

        # Check role is a valid number
        role = int(message.content[1:])
        if role < 0 or role > len(self.channel_info[message.channel.id]['roles']):
            sent = await message.channel.send('Invalid role number.')
            await message.delete(delay=5)
            await sent.delete(delay=5)
            return

        # Modify roles
        role = self.channel_info[message.channel.id]['roles'][role]
        if message.content[0] == '+':
            try:
                await message.author.add_roles(
                    role,
                    reason='kokobot message {} at {}'.format(message.id, message.created_at.timestamp()))
                log = 'Added "{}" role for {}.'.format(role.name, message.author)
                logger.info(log)
                sent = await message.channel.send(log)
                await sent.delete(delay=5)
            except discord.errors.Forbidden:
                sent = await message.channel.send('Not enough permissions to add "{}" role for {}. (Check role hierarchy)'.format(role.name, message.author))
                await sent.delete(delay=5)
            await message.delete(delay=5)
        elif message.content[0] == '-':
            try:
                await message.author.remove_roles(
                    role,
                    reason='kokobot message {} at {}'.format(message.id, message.created_at.timestamp()))
                log = 'Removed "{}" role for {}.'.format(role.name, message.author)
                logger.info(log)
                sent = await message.channel.send(log)
                await sent.delete(delay=5)
            except discord.errors.Forbidden:
                sent = await message.channel.send('Not enough permissions to remove "{}" role for {}. (Check role hierarchy)'.format(role.name, message.author))
                await sent.delete(delay=5)
            await message.delete(delay=5)
        else:
            sent = await message.channel.send('IT SHOULDNT GET HERE WTF JAY FIX IT ASAP')
            await message.delete(delay=5)
            await sent.delete(delay=5)

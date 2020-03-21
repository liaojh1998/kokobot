import datetime
import logging
import os

import discord
from discord.ext import commands

from . import cogs


def setup_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s [%(name)s]: %(message)s')

    # log to file
    os.makedirs('log', exist_ok=True)
    file_handler = logging.FileHandler(
        filename='log/{}.log'.format(int(datetime.datetime.utcnow().timestamp())),
        encoding='utf-8', mode='w')
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)

    # log to stderr
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.INFO)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    return logger

def run(
    client_id,
    token,
    owner_id=None,
    custom_cogs=[],
):
    logger = setup_logging()
    bot = commands.Bot(command_prefix='$', description="Kokobot for UT Austin SASE", owner_id=owner_id)
    permissions = discord.Permissions(permissions=0)

    # requested permissions
    permissions.manage_roles = True
    permissions.manage_nicknames = True
    permissions.manage_emojis = True
    permissions.view_channel = True
    permissions.send_messages = True
    permissions.manage_messages = True
    permissions.embed_links = True
    permissions.attach_files = True
    permissions.read_message_history = True
    permissions.mention_everyone = True
    permissions.use_external_emojis = True
    permissions.add_reactions = True
    permissions.connect = True

    # append cogs
    default_cogs = [
        cogs.Util,
        cogs.Roles,
        cogs.Koko,
    ]
    logger.info('Loading extensions:')
    for cog in default_cogs:
        cog = cog(bot)
        bot.add_cog(cog)
        logger.info('\t{}'.format(cog))
    for cog in custom_cogs:
        bot.load_extension(cog)
        logger.info('\t{}'.format(cog))
    logger.info('Done!')

    @bot.event
    async def on_ready():
        logger.info('--------------------------------------------------------')
        logger.info('Logged in as %s' % bot.user)
        logger.info('Invite me at: \n\n\t%s\n' % discord.utils.oauth_url(client_id, permissions=permissions))
        logger.info('--------------------------------------------------------')
        logger.info('Servers connected to:')
        for guild in bot.guilds:
            logger.info('\t%s' % guild.name)
            for channel in bot.guilds.channel:
                if channel.name == 'bot':
                    await channel.send('Kokobot is ready! Use `$help` for more information.')

    bot.run(token)

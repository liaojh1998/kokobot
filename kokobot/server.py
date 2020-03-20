import datetime
import logging
import os

import discord
from discord.ext import commands


def setup_logging():
    logger = logging.getLogger('discord')
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s:%(levelname)s [%(name)s]: %(message)s')

    # log to file
    os.makedirs('log', exist_ok=True)
    file_handler = logging.FileHandler(
        filename='log/{}.log'.format(int(datetime.datetime.now().timestamp())),
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

def run(client_id, token):
    logger = setup_logging()
    client = commands.Bot(command_prefix='$')
    permissions = discord.Permissions(permissions=1477962816)

    @client.event
    async def on_ready():
        logger.info('Logged in as %s' % client.user)
        logger.info('Invite me at: \n\n\t%s\n' % discord.utils.oauth_url(client_id, permissions=permissions))
        logger.info('Servers connected to:')
        for guild in client.guilds:
            logger.info('\t%s' % guild.name)

    client.run(token)

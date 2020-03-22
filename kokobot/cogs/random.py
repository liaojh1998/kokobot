import asyncio
import logging
import random as rng

import discord
from discord.ext import commands

logger = logging.getLogger('discord.kokobot.random')
emoji_bank = {
    ':regional_indicator_j:': '\U0001F1EF',
    ':regional_indicator_o:': '\U0001F1F4',
    ':regional_indicator_i:': '\U0001F1EE',
    ':regional_indicator_n:': '\U0001F1F3',
    ':twisted_rightwards_arrows:': '\U0001F500',
    ':octagonal_sign:': '\U0001F6D1',
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
        self.bot.add_listener(self.react, 'on_reaction_add')
        self.bot.add_listener(self.unreact, 'on_reaction_remove')

    async def clear_message(self, message, future):
        await asyncio.sleep(60)
        if not future.cancelled():
            if message.id in self.messages:
                self.messages.pop(message.id)
                await message.clear_reactions()
                embed = message.embeds[0]
                embed.description += "\n\nMixer has stopped."
                await message.edit(embed=embed)

    async def react(self, reaction, user):
        if (user == self.bot.user
                or not reaction.message.id in self.messages):
            return

        message = reaction.message
        if reaction.emoji == emoji_bank[':twisted_rightwards_arrows:']:
            # Shuffle
            await reaction.remove(user)
            if user in self.messages[message.id]['people']:
                if len(self.messages[message.id]['people']) == 0:
                    self.messages[message.id]['groups_list'] = None
                else:
                    self.messages[message.id]['groups_list'] = []
                    for _ in range(self.messages[message.id]['groups']):
                        self.messages[message.id]['groups_list'].append([])
                    shuffle = list(self.messages[message.id]['people'])
                    rng.shuffle(shuffle)
                    for i, p in enumerate(shuffle):
                        g = i % self.messages[message.id]['groups']
                        self.messages[message.id]['groups_list'][g].append(p)
                await self.mixer_display(self.messages[message.id]['message'],
                                         self.messages[message.id]['people'],
                                         self.messages[message.id]['groups'],
                                         self.messages[message.id]['groups_list'])
        elif reaction.emoji == emoji_bank[':octagonal_sign:']:
            # Stop
            await reaction.remove(user)
            if user == self.messages[message.id]['owner']:
                if 'future' in self.messages[message.id]:
                    self.messages[message.id]['future'].cancel()
                if message.id in self.messages:
                    self.messages.pop(message.id)
                    await message.clear_reactions()
                    embed = message.embeds[0]
                    embed.description += "\n\nMixer has stopped."
                    await message.edit(embed=embed)
        else:
            # Add user
            if not user in self.messages[message.id]['people']:
                self.messages[message.id]['people'].add(user)
                await self.mixer_display(self.messages[message.id]['message'],
                                         self.messages[message.id]['people'],
                                         self.messages[message.id]['groups'],
                                         self.messages[message.id]['groups_list'])

    async def unreact(self, reaction, user):
        if (user == self.bot.user
                or not reaction.message.id in self.messages):
            return

        if (reaction.emoji != emoji_bank[':twisted_rightwards_arrows:']
                and reaction.emoji != emoji_bank[':octagonal_sign:']):
            users = set()
            message = reaction.message
            for reaction in message.reactions:
                async for user in reaction.users():
                    if user != self.bot.user:
                        users.add(user)
            remove = []
            for p in self.messages[message.id]['people']:
                if not p in users:
                    remove.append(p)
            for p in remove:
                if p in self.messages[message.id]['people']:
                    self.messages[message.id]['people'].remove(p)
            if remove:
                await self.mixer_display(self.messages[message.id]['message'],
                                         self.messages[message.id]['people'],
                                         self.messages[message.id]['groups'],
                                         self.messages[message.id]['groups_list'])

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
        Only the owner of the mixer may shuffle and stop the mixer.
        """
        if groups < 2:
            await ctx.send('Invalid number of groups to mix.')
            return

        if groups > self.config['max_groups']:
            await ctx.send('Cannot mix more than {} groups.'.format(self.config['max_groups']))
            return

        # Create the embed
        title = f"Random Mixer for {groups} Groups"
        r = rng.randint(0, 255)
        b = rng.randint(0, 255)
        g = rng.randint(0, 255)
        colour = r*(16**4) + b*(16**2) + g
        embed = discord.Embed(title=title, description="Initializing...", colour=colour)
        embed.set_author(name=ctx.message.author, icon_url=ctx.message.author.avatar_url)
        message = await ctx.send(embed=embed)

        # Add reactions
        await message.add_reaction(emoji_bank[':regional_indicator_j:'])
        await message.add_reaction(emoji_bank[':regional_indicator_o:'])
        await message.add_reaction(emoji_bank[':regional_indicator_i:'])
        await message.add_reaction(emoji_bank[':regional_indicator_n:'])
        await message.add_reaction(emoji_bank[':twisted_rightwards_arrows:'])
        await message.add_reaction(emoji_bank[':octagonal_sign:'])

        # Add to messages
        self.messages[message.id] = {}
        self.messages[message.id]['message'] = message
        self.messages[message.id]['people'] = set()
        self.messages[message.id]['groups'] = groups
        self.messages[message.id]['groups_list'] = None
        self.messages[message.id]['owner'] = ctx.message.author

        # Display and enqueue future
        await self.mixer_display(self.messages[message.id]['message'],
                                 self.messages[message.id]['people'],
                                 self.messages[message.id]['groups'],
                                 self.messages[message.id]['groups_list'])

    async def mixer_display(self, message, people, groups, groups_list):
        if 'future' in self.messages[message.id]:
            self.messages[message.id]['future'].cancel()

        embed = message.embeds[0]
        desc = f"React on {emoji_bank[':regional_indicator_j:']} {emoji_bank[':regional_indicator_o:']} {emoji_bank[':regional_indicator_i:']} {emoji_bank[':regional_indicator_n:']} below to join, unreact to leave.\n"
        desc += f"Click {emoji_bank[':twisted_rightwards_arrows:']} to shuffle, {emoji_bank[':octagonal_sign:']} to stop.\n\n"

        # Add people
        if len(people) > 0:
            desc += "**People in this mixer:**\n"
            for p in people:
                desc += f"> {p}\n"
            desc += "\n"

        # Groups
        if not groups_list is None:
            for i in range(groups):
                if len(groups_list[i]) > 0:
                    desc += f"**Group {i+1}**\n"
                    for p in groups_list[i]:
                        desc += f"> {p}\n"
                    desc += "\n"

        embed.description = desc
        await message.edit(embed=embed)

        future = asyncio.Future()
        self.messages[message.id]['future'] = future
        await self.clear_message(self.messages[message.id]['message'],
                                 future)

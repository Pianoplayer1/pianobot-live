from datetime import datetime, timedelta, timezone
from math import floor, log10

from discord.ext.commands import Bot, Cog, Context, command
from discord.utils import format_dt
from setuptools.extern import names

from pianobot import Pianobot
from pianobot.utils import paginator


class GuildXP(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        aliases=('guildXp', 'xp'),
        brief='Returns the guild xp contributed by Eden members.',
        help=(
            'This command gives a list of contributed guild xp per member.'
            ' You can specify an interval as two decimal numbers, which will be interpreted'
            ' as the number of days ago.\n\n'
            '**Example**\n`gxp 7 0.5` will show the xp gained between 7 days and 12 hours ago.'
        ),
        name='gxp',
        usage='[days since start] [days since end]',
    )
    async def gxp(self, ctx: Context[Bot], *, arg: str = '') -> None:
        args = arg.split() or ['']
        if len(args) > 0 and args[0].lower() in ('e', 'emeralds', 'p', 'pending'):
            if len(args) > 2 and args[1].lower() in ('s', 'set'):
                if ctx.author.guild_permissions.administrator:
                    try:
                        amount = int(args[2])
                        with open('xp_emeralds.txt', 'w') as f:
                            f.write(str(amount))
                    except ValueError:
                        await ctx.send('Input a valid number of emeralds per 1B xp!')
                    else:
                        await ctx.send(f'Every step of 1B xp will now reward `{amount}` emeralds (`{round(amount / 4096, 2)}` LE).')
                else:
                    await ctx.send('You do not have the required permissions to set the xp reward amount.')
                return
            if len(args) >= 2 and args[1].lower() in ('r', 'reset'):
                if len(args) < 3:
                    await ctx.send('Please specify a user to reset the xp rewards for.')
                elif ctx.author.guild_permissions.administrator:
                    if await self.bot.database.raid_members.reset_xp(args[2]):
                        await ctx.send(f'Pending emeralds of `{args[2]}` have been reset.')
                    else:
                        await ctx.send(f'Username `{args[2]}` not found.')
                else:
                    await ctx.send('You do not have the required permissions to reset the xp rewards.')
                return
            results = await self.bot.database.raid_members.get_xp()
            if results:
                data = [
                    [name, display(amount), str(le // 4096)]
                    for name, amount, le in sorted(list(results.items()), key=lambda x: (x[2], x[1]))
                ]
                columns = {'Username': 19, 'Amount': 15, 'Pending LE': 12}
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('There are no pending xp rewards.')
        else:
            args = list(map(str.lower, args))
            now = datetime.now(timezone.utc)
            times = []
            for a in args:
                try:
                    times.append(float(a))
                except ValueError:
                    pass
            start = now - timedelta(days=times[0]) if times else None
            end = now - timedelta(days=times[1]) if len(times) > 1 else None
            results = await self.bot.database.guild_xp.get_between(start, end)
            if results:
                data = [
                    [name, display(count)]
                    for name, count in sorted(list(results.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 19, 'Amount': 15}
                message = f'Guild xp contributions'
                if start and not end:
                    message += f' since {format_dt(start, style="D")}'
                elif start and end:
                    message += f' between {format_dt(start, style="D")} and {format_dt(end, style="D")}'
                await ctx.send(message + ':')
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No guild xp gained in this interval.')


def display(num: int | float) -> str:
    names = ['', ' Thousand', ' Million', ' Billion', ' Trillion']
    pos = max(
        0,
        min(len(names) - 1, int(floor(0 if num == 0 else log10(abs(num)) / 3))),
    )
    return f'{num / 10 ** (3 * pos):.2f}{names[pos]}'


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(GuildXP(bot))

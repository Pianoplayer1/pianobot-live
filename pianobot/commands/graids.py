from datetime import datetime, timedelta, timezone

from discord.ext.commands import Bot, Cog, Context, command
from discord.utils import format_dt

from pianobot import Pianobot
from pianobot.utils import paginator


RAIDS = {
    'Nest of the Grootslangs': {'notg', 'nog'},
    'Orphion\'s Nexus of Light': {'nol', 'onol'},
    'The Canyon Colossus': {'tcc'},
    'The Nameless Anomaly': {'tna'},
}

ASPECT_ROLES = (682677588933869577, 727551690248683571, 682675116865224773, 727549491699253379)


class GuildRaids(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        brief='Returns the guild raids done by Eden members.',
        help=(
            'This command gives a list of completed guild raids per member.'
            ' You can specify an interval as two decimal numbers, which will be interpreted'
            ' as the number of days ago.\n'
            'Additionally, you can specify a raid to only show the results for that raid.\n\n'
            '**Example**\n`graids tcc 7 0.5` will show the TCCs done between 7 days and 12 hours ago.'
        ),
        name='graids',
        usage='[raid] [days since start] [days since end]',
    )
    async def graids(self, ctx: Context[Bot], *, arg: str = '') -> None:
        args = arg.split() or ['']
        if len(args) > 0 and args[0].lower() in ('e', 'emeralds', 'p', 'pending'):
            if len(args) >= 2 and args[1].lower() in ('l', 'left'):
                raids = await self.bot.database.raid_members.get_pending_left()
                if raids:
                    data = [
                        [raid, str(count // 4096)]
                        for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                    ]
                    columns = {'UUID': 40, 'Pending LE': 12}
                    await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
                else:
                    await ctx.send('No pending emeralds of former guild members.')
                return
            if len(args) > 2 and args[1].lower() in ('s', 'set'):
                if ctx.author.guild_permissions.administrator:
                    try:
                        amount = int(args[2])
                        with open('emeralds.txt', 'w') as f:
                            f.write(str(amount))
                    except ValueError:
                        await ctx.send('Input a valid number of emeralds per raid!')
                    else:
                        await ctx.send(f'Each raid will now reward `{amount}` emeralds (`{round(amount / 4096, 2)}` LE).')
                else:
                    await ctx.send('You do not have the required permissions to set the raid reward amount.')
                return
            if len(args) >= 2 and args[1].lower() in ('r', 'reset'):
                if len(args) < 3:
                    await ctx.send('Please specify a user to reset the raids for.')
                elif ctx.author.guild_permissions.administrator:
                    if await self.bot.database.raid_members.reset_pending(args[2]):
                        await ctx.send(f'Pending emeralds of `{args[2]}` have been reset.')
                    else:
                        await ctx.send(f'Username `{args[2]}` not found.')
                else:
                    await ctx.send('You do not have the required permissions to reset the raids.')
                return
            raids = await self.bot.database.raid_members.get_pending()
            if raids:
                data = [
                    [raid, str(count // 4096)]
                    for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 22, 'Pending LE': 12}
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No new raids have been logged.')
        elif len(args) > 0 and args[0].lower() in ('a', 'aspects'):
            if len(args) >= 2 and args[1].lower() in ('l', 'left'):
                raids = await self.bot.database.raid_members.get_aspects_left()
                if raids:
                    data = [
                        [raid, str(count // 2)]
                        for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                    ]
                    columns = {'UUID': 40, 'Pending Aspects': 17}
                    await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
                else:
                    await ctx.send('No pending aspects of former guild members.')
                return
            if len(args) >= 2 and args[1].lower() in ('r', 'reset'):
                if any(r for r in ctx.author.roles if r.id in ASPECT_ROLES):
                    if len(args) < 3:
                        await ctx.send('Please specify a user (or `all`) to reset the raids for.')
                    elif args[2] == 'all':
                        await self.bot.database.raid_members.reset_aspects()
                        await ctx.send(f'All pending aspects have been reset.')
                    else:
                        if await self.bot.database.raid_members.reset_aspects(args[2]):
                            await ctx.send(f'Pending aspects of `{args[2]}` have been reset.')
                        else:
                            await ctx.send(f'Username `{args[2]}` not found.')
                else:
                    await ctx.send('You do not have the required permissions to reset the raids.')
                return
            if len(args) >= 2 and args[1].lower() in ('a', 'allow'):
                if any(r for r in ctx.author.roles if r.id in ASPECT_ROLES):
                    if len(args) < 3:
                        await ctx.send('Please specify a user to allow aspects for.')
                    else:
                        if await self.bot.database.raid_members.set_aspects(args[2], 0):
                            await ctx.send(f'`{args[2]}` is now receiving aspects again.')
                        else:
                            await ctx.send(f'Username `{args[2]}` not found.')
                else:
                    await ctx.send('You do not have the required permissions to manage aspects.')
                return
            if len(args) >= 2 and args[1].lower() in ('b', 'block'):
                if any(r for r in ctx.author.roles if r.id in ASPECT_ROLES):
                    if len(args) < 3:
                        blocked_members = await self.bot.database.raid_members.get_blocked_aspects()
                        if blocked_members:
                            await ctx.send('Blocked members:\n' + '\n'.join(sorted(blocked_members)))
                        else:
                            await ctx.send('No members are currently blocked from receiving aspects.')
                    else:
                        if await self.bot.database.raid_members.set_aspects(args[2], -1):
                            await ctx.send(f'`{args[2]}` is now no longer receiving aspects.')
                        else:
                            await ctx.send(f'Username `{args[2]}` not found.')
                else:
                    await ctx.send('You do not have the required permissions to manage aspects.')
                return
            raids = await self.bot.database.raid_members.get_aspects()
            if raids:
                data = [
                    [raid, str(count // 2)]
                    for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 22, 'Pending Aspects': 17}
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No new raids have been logged.')
        elif len(args) > 1 and args[1].lower() in ('r', 'reset'):
            await ctx.send('Reset pending emeralds with `-graids e r <name>` or pending aspects with `-graids a r <name>`.')
        else:
            args = list(map(str.lower, args))
            now = datetime.now(timezone.utc)
            raid = next((r for r, v in RAIDS.items() if any(s in args for s in v)), None)
            times = []
            for a in args:
                try:
                    times.append(float(a))
                except ValueError:
                    pass
            start = now - timedelta(days=times[0]) if times else None
            end = now - timedelta(days=times[1]) if len(times) > 1 else None
            if raid is None:
                results = await self.bot.database.raid_log.get_between(start, end)
            else:
                results = await self.bot.database.raid_log.get_specific_between(raid, start, end)
            if results:
                data = [
                    [raid, str(count)]
                    for raid, count in sorted(list(results.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 22, 'Amount': 8}
                message = f'{raid or "Guild raid"} completions'
                if start and not end:
                    message += f' since {format_dt(start, style="D")}'
                elif start and end:
                    message += f' between {format_dt(start, style="D")} and {format_dt(end, style="D")}'
                await ctx.send(message + ':')
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No guild raids in this interval.')


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(GuildRaids(bot))

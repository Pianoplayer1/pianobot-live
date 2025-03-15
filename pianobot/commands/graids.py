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
        if arg.lower() in ('p', 'pending'):
            raids = await self.bot.database.raid_log.get_new()
            if raids:
                data = [
                    [raid, str(count)]
                    for raid, count in sorted(list(raids.items()), key=lambda x: x[1])
                ]
                columns = {'Username': 22, 'Amount': 8}
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No new raids have been logged.')
        elif arg.lower() in ('r', 'reset') and ctx.guild:
            if ctx.author.guild_permissions.administrator:
                await self.bot.database.raid_log.reset_new()
                await ctx.send('All raids have been reset.')
            else:
                await ctx.send('You do not have the required permissions to reset the raids.')
            return
        else:
            now = datetime.now(timezone.utc)
            args = arg.lower().split()
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
                    message += f' since {format_dt(start, style="D")}:'
                elif start and end:
                    message += f' between {format_dt(start, style="D")} and {format_dt(end, style="D")}:'
                await ctx.send(message)
                await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
            else:
                await ctx.send('No guild raids in this interval.')


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(GuildRaids(bot))

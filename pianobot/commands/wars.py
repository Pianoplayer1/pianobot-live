from datetime import datetime, timedelta, timezone

from discord.ext.commands import Bot, Cog, Context, command
from discord.utils import format_dt

from pianobot import Pianobot
from pianobot.utils import paginator


class GuildWars(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        brief='Returns the guild wars done by Eden members.',
        help=(
            'This command gives a list of completed guild wars per member.'
            ' You can specify an interval as two decimal numbers, which will be interpreted'
            ' as the number of days ago.\n\n'
            '**Example**\n`wars 7 0.5` will show the wars done between 7 days and 12 hours ago.'
        ),
        name='wars',
        usage='[days since start] [days since end]',
    )
    async def wars(self, ctx: Context[Bot], *, arg: str = '') -> None:
        args = list(map(str.lower, arg.split() or ['']))
        now = datetime.now(timezone.utc)
        times = []
        for a in args:
            try:
                times.append(float(a))
            except ValueError:
                pass
        start = now - timedelta(days=times[0]) if times else None
        end = now - timedelta(days=times[1]) if len(times) > 1 else None
        results = await self.bot.database.war_log.get_between(start, end)
        if results:
            data = [
                [war, str(count)]
                for war, count in sorted(list(results.items()), key=lambda x: x[1])
            ]
            columns = {'Username': 22, 'Amount': 8}
            message = f'Guild war completions'
            if start and not end:
                message += f' since {format_dt(start, style="D")}'
            elif start and end:
                message += f' between {format_dt(start, style="D")} and {format_dt(end, style="D")}'
            await ctx.send(message + ':')
            await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)
        else:
            await ctx.send('No guild wars in this interval.')


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(GuildWars(bot))

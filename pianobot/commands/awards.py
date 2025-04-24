from datetime import datetime, timedelta, timezone

from discord.ext.commands import Bot, Cog, Context, command
from discord.utils import format_dt

from pianobot import Pianobot
from pianobot.utils import get_cycle, paginator, display_full


class Awards(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        brief='Shows the leaderboards for raids, wars and guild xp in the current promotion cycle',
        help=(
            'This command displays leaderboards for the relevant stats for Eden\'s bi-monthly awards: The number of '
            'raids completed, the number of successful wars and the amount of contributed xp. All of these statistics '
            'are computed for the current promotion cycle, meaning only the progress since the last cycle is counted. '
            'You can specify which of these three stats you want the results to be sorted by.'
        ),
        name='awards',
        usage='[type]',
    )
    async def awards(self, ctx: Context[Bot], *, sort_by: str = 'raids') -> None:
        dt = datetime.now(timezone.utc)
        current_cycle = get_cycle(dt)
        prev_cycle = get_cycle(dt - timedelta(days=20 if 8 < dt.day < 15 or 22 < dt.day else 10))

        if dt.day < 15:
            start_date = datetime(dt.year, dt.month, 1, tzinfo=timezone.utc)
            end_date = datetime(dt.year, dt.month, 15, tzinfo=timezone.utc)
        else:
            start_date = datetime(dt.year, dt.month, 15, tzinfo=timezone.utc)
            end_date = datetime(dt.year + dt.month // 12, (dt.month + 1) % 12, 1, tzinfo=timezone.utc)

        results = await self.bot.database.guild_award_stats.get_for_cycle(current_cycle)
        prev_results = await self.bot.database.guild_award_stats.get_for_cycle(prev_cycle)
        # prev_raids = {entry.username: entry.raid_count for entry in prev_results}
        raid_results = await self.bot.database.raid_log.get_between(start_date)
        prev_wars = {entry.username: entry.wars for entry in prev_results}
        prev_xp = {entry.username: entry.xp for entry in prev_results}

        data_raw = [
            (
                entry.username,
                # entry.raid_count - prev_raids.get(entry.username, 0),
                raid_results.get(entry.username, 0),
                entry.wars - prev_wars.get(entry.username, 0),
                entry.xp - prev_xp.get(entry.username, 0) if prev_xp.get(entry.username, 0) <= entry.xp else entry.xp,
            )
            for entry in results
        ]

        if 'xp' in sort_by:
            data_raw.sort(key=lambda x: (x[3], x[1], x[2]))
        elif 'war' in sort_by:
            data_raw.sort(key=lambda x: (x[2], x[1], x[3]))
        else:
            data_raw.sort(key=lambda x: (x[1], x[2], x[3]))

        data = [[d[0], str(d[1]), str(d[2]), display_full(d[3])] for d in data_raw]

        text = f'Current Eden Award leaderboards, sorted by {sort_by}.\n'
        text += f'This promotion cycle will end on {format_dt(end_date)}'
        await ctx.send(text)

        columns = {'Username': 22, 'Guild Raids': 14, 'Wars': 14, 'Guild XP': 20}
        await paginator(ctx, data, columns)


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(Awards(bot))

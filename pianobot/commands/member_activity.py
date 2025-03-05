from datetime import datetime, timezone

from discord.ext.commands import Bot, Cog, Context, command

from pianobot import Pianobot
from pianobot.utils import paginator


class MemberActivity(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        aliases=['mAct'],
        brief='Outputs the member activity times of Eden for a calendar week.',
        help=(
            'This command returns a table with the times each member of Eden has been active on'
            ' the Wynncraft server. Optionally, use a week number and a year to get activity times'
            ' of a certain week.'
        ),
        name='memberActivity',
        usage='[calendar week] [year]',
    )
    async def member_activity(
        self, ctx: Context[Bot], week: int | None = None, year: int | None = None
    ) -> None:
        iso_date = datetime.now(timezone.utc).isocalendar()
        if week is None:
            week = iso_date.week
        if year is None:
            year = iso_date.year
        date = f'{year}-{week}'
        if date not in await self.bot.database.member_activity.get_weeks():
            await ctx.send('No data available for the specified interval!')
            return

        activity_data = []
        guild = await self.bot.corkus.guild.get('Eden')
        for username, time in (await self.bot.database.member_activity.get(date)).items():
            member = next(
                (member for member in guild.members if member.username == username), None
            )
            if member is None:
                continue
            activity_data.append(
                (
                    time,
                    (
                        username,
                        'Unknown' if member is None else member.rank.value.title(),
                        f'{time} minutes'
                        if time < 60
                        else f'{int(time / 60):02}:{time % 60:02} hours',
                    ),
                )
            )

        columns = {'Eden Members': 36, 'Rank': 26, 'Time Online': 26}
        results = [list(res[1]) for res in sorted(activity_data, key=lambda item: item[0])]
        await paginator(ctx, results, columns)


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(MemberActivity(bot))

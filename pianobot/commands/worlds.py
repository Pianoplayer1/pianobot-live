from datetime import datetime, timezone
from math import floor

from discord.ext.commands import Bot, Cog, Context, command

from pianobot import Pianobot
from pianobot.utils import paginator


class Soulpoints(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        brief='Returns a list of the current Wynncraft worlds.',
        help=(
            'This command gives you a list of all current Wynncraft worlds, sorted by their uptime.'
        ),
        name='worlds',
    )
    async def worlds(self, ctx: Context[Bot]) -> None:
        now = datetime.now(timezone.utc)
        worlds = [
            (str(world.name), (now - world.started_at).seconds)
            for world in await self.bot.database.worlds.get_all()
        ]
        worlds = sorted(worlds, key=lambda item: item[1])
        data = [
            [
                world,
                'North America' if world.startswith('NA') else ('Europe' if world.startswith('EU') else 'Unknown'),
                f'{floor(uptime / 3600):02}:{floor(uptime % 3600 / 60):02} hours',
            ]
            for world, uptime in worlds
        ]
        columns = {'Server': 10, 'Region': 18, 'Uptime': 18}
        await paginator(ctx, data, columns, page_rows=20, separator_rows=0, enum=False)


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(Soulpoints(bot))
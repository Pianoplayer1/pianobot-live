from uuid import uuid4

from corkus.errors import BadRequest
from discord import Embed
from discord.ext.commands import Bot, Cog, Context, command

from pianobot import Pianobot


class PlayerActivity(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        aliases=['pAct'],
        brief='Outputs the activity of a given player in a given interval.',
        help=(
            'This command returns a bar graph with the number of minutes a given player has been'
            ' online in the last days (up to two weeks).'
        ),
        name='playerActivity',
        usage='<player> [days]',
    )
    async def pact(self, ctx: Context[Bot], player: str, interval: str = '13') -> None:
        if interval.startswith('-'):
            interval = interval[1:]
        try:
            int_interval = int(interval)
        except ValueError:
            await ctx.send('Please provide a valid interval!')
            return

        try:
            wynn_player = await self.bot.corkus.player.get(player)
        except BadRequest:
            await ctx.send('Not a valid Wynncraft player!')
            return

        embed = Embed()
        embed.set_author(
            icon_url=f'https://mc-heads.net/head/{wynn_player.username}.png',
            name=wynn_player.username,
        )
        embed.set_image(
            url=(
                'https://wynnstats.endoy.dev/api/charts'
                f'/onlinetime/{wynn_player.username}/{int_interval}?caching={uuid4()}'
            )
        )
        embed.set_footer(text='Player tracking from \'WynnStats\' by Dieter Blancke')
        await ctx.send(embed=embed)


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(PlayerActivity(bot))

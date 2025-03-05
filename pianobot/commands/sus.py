from datetime import datetime, timezone
from math import floor

from corkus.errors import BadRequest
from corkus.objects import PlayerTag
from discord import Colour, Embed
from discord.ext.commands import Bot, Cog, Context, command

from pianobot import Pianobot


class Sus(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        aliases=['alt'],
        brief='Check the suspiciousness of a player.',
        help='View the approximate probability of a player being an alt account.',
        name='sus',
        usage='<player>',
    )
    async def sus(self, ctx: Context[Bot], player: str) -> None:
        async with ctx.typing():
            try:
                player_data = await self.bot.corkus.player.get(player)
            except BadRequest:
                await ctx.send('Not a valid Wynncraft player!')
                return

            embed = Embed(description=f'## Suspiciousness of {player_data.username}: ', timestamp=datetime.now(timezone.utc))
            embed.set_footer(text='Pianobot')
            embed.set_thumbnail(url=f'https://visage.surgeplay.com/face/{player_data.uuid.string()}')

            total_score = 0.0
        total_score += add_embed_field(
            embed,
            'Join Date',
            (datetime.now(timezone.utc) - player_data.join_date).days,
            500,
            player_data.join_date.strftime('%b %d, %Y'),
        )
        total_score += add_embed_field(
            embed,
            'Rank',
            {PlayerTag.PLAYER: 50, PlayerTag.VIP: 80}.get(player_data.tag, 100),
            100,
            f'[{player_data.tag.value}]',
        )
        total_score += add_embed_field(
            embed,
            'Total Playtime',
            player_data.playtime.hours(4.7),
            500,
            f'{floor(player_data.playtime.hours(4.7))} Hours',
        )
        total_score += add_embed_field(embed, 'Total Level', player_data.combined_level, 1000)
        total_score += add_embed_field(
            embed, 'Quests', len([q for c in player_data.characters for q in c.quests]), 300
        )
        total_score += add_embed_field(
            embed,
            'Dungeons & Raids',
            sum([x.completed for x in player_data.dungeons + player_data.raids]),
            200,
        )
        total_score /= 6

        if embed.description is not None:
            embed.description += f'{total_score:.2f}%'
        red = 255 if total_score >= 25 else round(255 * total_score / 25)
        green = 255 if total_score <= 75 else round(255 * (total_score - 75) / 25)
        embed.colour = Colour((red << 16) + (green << 8))

        await ctx.send(embed=embed)


def add_embed_field(
    embed: Embed, title: str, value: float, max_value: int, text: str | None = None
) -> float:
    sus_score = 100 - min(100 * value / max_value, 100)
    embed.add_field(name=title, value=f'```hs\n{text or value:<12}\n{round(sus_score, 2)}% sus```')
    return sus_score


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(Sus(bot))

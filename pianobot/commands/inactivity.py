from asyncio import gather

from corkus.objects.member import Member
from datetime import datetime, timezone
from discord import Interaction, Message
from discord.ext.commands import Bot, Cog, Context, command
from discord.ui import Select, View, select

from pianobot import Pianobot
from pianobot.utils import paginator


class Inactivity(Cog):
    def __init__(self, bot: Pianobot) -> None:
        self.bot = bot

    @command(
        aliases=['act', 'activity', 'inact'],
        brief='Outputs the member inactivity times of a specified guild.',
        help=(
            'This command returns a table with the times since each member of a specified guild'
            ' has been last seen on the Wynncraft server.'
        ),
        name='inactivity',
        usage='<guild>',
    )
    async def inactivity(self, ctx: Context[Bot], *, guild: str) -> None:
        async with ctx.typing():
            guilds = [g.name for g in await self.bot.corkus.guild.list_all()]
            if guild in guilds:
                await self.inactivity_for(guild, ctx)
                return

            full_matches = []
            partial_matches = []
            for guild_name in guilds:
                if guild.lower() == guild_name.lower():
                    full_matches.append(guild_name)
                elif guild.lower() in guild_name.lower():
                    partial_matches.append(guild_name)

            matches = full_matches or partial_matches
            if len(matches) == 0:
                await ctx.send(
                    f'No guild names include `{guild}`. Please try again with a correct guild'
                    ' name.'
                )
            elif len(matches) == 1:
                await self.inactivity_for(matches[0], ctx)
            elif len(matches) <= 5:
                await ctx.send(
                    f'Several guild names include `{guild}`, please select the one you meant:',
                    view=SelectMenu(matches, self, ctx),
                )
            else:
                await ctx.send(
                    f'{len(matches)} guild names include `{guild}`. Please try again with a more'
                    ' precise name.'
                )

    async def inactivity_for(
        self, guild: str, ctx: Context[Bot], message: Message | None = None
    ) -> None:
        guild_stats = await self.bot.corkus.guild.get(guild)
        guild_uuids = {m.uuid for m in guild_stats.members}
        db_stats = {p.uuid: p for p in await self.bot.database.players.get_selected(guild_uuids)}

        inactivity_data: list[tuple[float, list[str]]] = await gather(
            *[self.fetch(member, db_stats) for member in guild_stats.members]
        )
        results = [result[1] for result in sorted(inactivity_data, key=lambda item: item[0])]

        columns = {f'{guild} Members': 36, 'Rank': 26, 'Time Inactive': 26}
        await paginator(ctx, results, columns, message=message)

    async def fetch(self, member: Member, db_stats: dict) -> tuple[float, list[str]]:
        db_player = db_stats.get(member.uuid, None)
        if db_player is not None:
            raw_days, display_time = format_last_seen(False, db_player.last_seen)
        else:
            player = await member.fetch_player()
            await self.bot.database.players.add(player.uuid, player.last_online)
            raw_days, display_time = format_last_seen(player.online, player.last_online)

        return raw_days, [member.username, member.rank.value.title(), display_time]


class SelectMenu(View):
    def __init__(self, guilds: list[str], cog: Inactivity, ctx: Context[Bot]) -> None:
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        for guild in sorted(guilds):
            self.select_menu.add_option(label=guild, value=guild)

    @select()
    async def select_menu(self, interaction: Interaction, menu: Select[View]) -> None:
        menu.disabled = True
        menu.placeholder = menu.values[0]
        await interaction.response.edit_message(view=self)
        await self.cog.inactivity_for(menu.values[0], self.ctx, interaction.message)


def format_last_seen(online: bool, last_online: datetime) -> tuple[float, str]:
    diff = datetime.now(timezone.utc) - last_online
    if online or diff.seconds < 30:
        days_offline = 0.0
        display_time = 'Online'
    else:
        days_offline = diff.days + (diff.seconds / 86400)
        value = days_offline
        unit = 'day'
        if value < 3:
            value *= 24
            unit = 'hour'
            if value < 1:
                value *= 60
                unit = 'minute'
        if round(value) != 1:
            unit += 's'
        display_time = f'{round(value)} {unit}'
    return days_offline, display_time


async def setup(bot: Pianobot) -> None:
    await bot.add_cog(Inactivity(bot))

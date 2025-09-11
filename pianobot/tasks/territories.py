from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusException
from discord import Embed, TextChannel

if TYPE_CHECKING:
    from pianobot import Pianobot


async def territories(bot: Pianobot) -> None:
    db_terrs = {terr.name: terr for terr in await bot.database.territories.get_all()}

    try:
        wynn_territories = await bot.corkus.territory.list_all()
    except CorkusException as e:
        getLogger('tasks.territories').warning('Error when fetching list of territories: %s', e)
        return

    try:
        eden = await bot.corkus.guild.get('Eden')
    except CorkusException as e:
        getLogger('tasks.territories').warning(
            'Error when fetching guild data of `Eden` and list of online players: %s', e
        )
        return
    highest_rank = max(
        (int(member.rank) for member in eden.members if member.is_online),
        default=-1,
    )

    async def send_territory_message(terr_name: str, old_guild: str, new_guild: str, time_held: timedelta) -> None:
        value = time_held.days + (time_held.seconds / 86400)
        unit = 'day'
        if value < 3:
            value *= 24
            unit = 'hour'
            if value < 1:
                value *= 60
                unit = 'minute'
        value = round(value)
        if value != 1:
            unit += 's'

        old_count = sum(1 for t in wynn_territories if t.guild and t.guild.name == old_guild)
        new_count = sum(1 for t in wynn_territories if t.guild and t.guild.name == new_guild)

        embed = Embed(
            color=0x00aa00 if new_guild == 'Eden' else 0xaa0000,
            title=':crossed_swords:   Territory ' + ('captured' if new_guild == 'Eden' else 'lost'),
            description=f"{old_guild} ({old_count})\n:arrow_forward:  {new_guild} ({new_count})",
        )
        embed.set_author(name=terr_name)
        embed.set_footer(text=f'Held for {value} {unit}')

        for server in await bot.database.servers.get_all():
            if server.territory_log_channel is None:
                continue
            if (
                    server.ping_interval is not None
                    and server.ping_role is not None
                    and datetime.now(timezone.utc)
                    >= (server.last_ping or datetime.min.replace(tzinfo=timezone.utc))
                    + timedelta(minutes=server.ping_interval)
                    and (6 if server.ping_rank is None else server.ping_rank) > highest_rank
            ):
                ping = f'<@&{server.ping_role}>'
                await bot.database.servers.update_last_ping(
                    server.server_id, datetime.now(timezone.utc)
                )
            else:
                ping = None
            channel = bot.get_channel(server.territory_log_channel)
            if isinstance(channel, TextChannel):
                await channel.send(ping, embed=embed)
            else:
                getLogger('tasks.territories').warning(
                    'Channel %s not found', server.territory_log_channel
                )

    for territory in wynn_territories:
        guild_name = None if territory.guild is None else territory.guild.name
        if territory.name not in db_terrs.keys():
            await bot.database.territories.add(territory, guild_name, territory.acquired)
            continue
        if db_terrs[territory.name].guild != guild_name:
            await bot.database.territories.update(territory.name, guild_name, territory.acquired)
            if db_terrs[territory.name].guild == 'Eden' or guild_name == 'Eden':
                await send_territory_message(
                    territory.name,
                    db_terrs[territory.name].guild,
                    guild_name,
                    territory.acquired - db_terrs[territory.name].acquired
                )

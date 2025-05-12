from __future__ import annotations

from datetime import datetime, timedelta, timezone
from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusException
from discord import TextChannel

if TYPE_CHECKING:
    from pianobot import Pianobot


async def territories(bot: Pianobot) -> None:
    db_terrs = {terr.name: terr for terr in await bot.database.territories.get_all()}
    notify = None
    missing = []
    try:
        wynn_territories = await bot.corkus.territory.list_all()
    except CorkusException as e:
        getLogger('tasks.territories').warning('Error when fetching list of territories: %s', e)
        return

    for territory in wynn_territories:
        guild_name = None if territory.guild is None else territory.guild.name
        if territory.name not in db_terrs.keys():
            continue
        if db_terrs[territory.name].guild != guild_name:
            await bot.database.territories.update(territory.name, guild_name)
        if guild_name != 'Eden':
            missing.append(territory)
            if db_terrs[territory.name].guild == 'Eden' and territory.guild is not None:
                notify = territory
    if len(missing) == 0 and any(terr.guild != 'Eden' for terr in db_terrs.values()):
        for server in await bot.database.servers.get_all():
            if server.territory_log_channel is not None:
                channel = bot.get_channel(server.territory_log_channel)
                if isinstance(channel, TextChannel):
                    await channel.send('Fully reclaimed!')
                else:
                    getLogger('tasks.territories').warning(
                        'Channel %s not found', server.territory_log_channel
                    )
    if notify is None:
        return

    terrs_msg = '\n'.join([f'- {terr.name} ({terr.guild.name})' for terr in missing][:10])
    if len(missing) > 10:
        terrs_msg += f'\n- ... ({len(missing) - 10} more)'
    msg = (
        f'{notify.guild.name if notify.guild is not None else None} has taken control of'
        f' {notify.name}!```All missing territories ({len(missing)}):\n\n{terrs_msg}```'
    )

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

    for server in await bot.database.servers.get_all():
        if server.territory_log_channel is None:
            continue
        temp_msg = msg
        if (
            server.ping_interval is not None
            and server.ping_role is not None
            and datetime.now(timezone.utc)
            >= (server.last_ping or datetime.min.replace(tzinfo=timezone.utc))
            + timedelta(minutes=server.ping_interval)
            and (6 if server.ping_rank is None else server.ping_rank) > highest_rank
        ):
            temp_msg = f'<@&{server.ping_role}>\n{msg}'
            await bot.database.servers.update_last_ping(
                server.server_id, datetime.now(timezone.utc)
            )
        channel = bot.get_channel(server.territory_log_channel)
        if isinstance(channel, TextChannel):
            await channel.send(temp_msg)
        else:
            getLogger('tasks.territories').warning(
                'Channel %s not found', server.territory_log_channel
            )

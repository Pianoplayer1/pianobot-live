from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusTimeoutError

if TYPE_CHECKING:
    from pianobot import Pianobot

async def players(bot: Pianobot) -> None:
    try:
        online_players = await bot.corkus.network.online_players(by_uuid=True)
        uuids = {player.uuid for player in online_players.uuid_players}
    except CorkusTimeoutError:
        getLogger('tasks.guild_activity').warning('Error when fetching list of online players')
        return

    db_uuids = {p.uuid for p in await bot.database.players.get_selected(uuids)}

    to_add = uuids - db_uuids
    if to_add:
        await bot.database.players.add_multiple(to_add)
    if db_uuids:
        await bot.database.players.update_last_seen(db_uuids)

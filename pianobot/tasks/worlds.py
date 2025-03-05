from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

from corkus.errors import CorkusException

if TYPE_CHECKING:
    from pianobot import Pianobot


async def worlds(bot: Pianobot) -> None:
    world_names = {world.name for world in await bot.database.worlds.get_all()}
    try:
        online_players = await bot.corkus.network.online_players()
    except CorkusException as e:
        getLogger('tasks.worlds').warning('Error when fetching list of online players: %s', e)
        return

    for server in online_players.servers:
        if server.name in world_names:
            world_names.remove(server.name)
        elif server.name is not None:
            await bot.database.worlds.add(server.name)

    for world in world_names:
        await bot.database.worlds.remove(world)

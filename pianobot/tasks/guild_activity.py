from __future__ import annotations

from asyncio import gather
from logging import getLogger
from typing import TYPE_CHECKING

from corkus import Corkus
from corkus.errors import BadRequest, CorkusTimeoutError
from corkus.objects.online_players import OnlinePlayers

if TYPE_CHECKING:
    from pianobot import Pianobot

async def guild_activity(bot: Pianobot) -> None:
    guilds: dict[str, int | None] = {guild: None for guild in bot.tracked_guilds}
    try:
        online_players = await bot.corkus.network.online_players()
        players = {player.username for player in online_players.players}
    except CorkusTimeoutError:
        getLogger('tasks.guild_activity').warning('Error when fetching list of online players')
        return

    for result in await gather(*[fetch(bot.corkus, guild, players) for guild in guilds]):
        if result is not None:
            guilds.update(result)

    await bot.database.guild_activity.add(guilds)


async def fetch(corkus: Corkus, name: str, players: set[str | None]) -> dict[str, int] | None:
    try:
        guild = await corkus.guild.get(name)
        return {guild.name: sum(member.username in players for member in guild.members)}
    except (BadRequest, CorkusTimeoutError):
        getLogger('tasks.guild_activity').warning('Error when fetching guild data of `%s`', name)
        return None

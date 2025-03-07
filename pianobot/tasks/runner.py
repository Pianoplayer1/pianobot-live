from __future__ import annotations

from logging import getLogger
from time import perf_counter
from typing import Any, Callable, Coroutine, TYPE_CHECKING

from discord.ext.tasks import loop

from pianobot.tasks.guild_activity import guild_activity
from pianobot.tasks.guild_awards import guild_awards
from pianobot.tasks.guild_raids import guild_raids
from pianobot.tasks.guild_xp import guild_xp
from pianobot.tasks.member_activity import member_activity
from pianobot.tasks.members import members
from pianobot.tasks.players import players
from pianobot.tasks.territories import territories
from pianobot.tasks.worlds import worlds

if TYPE_CHECKING:
    from pianobot import Pianobot


class TaskRunner:
    def __init__(self, bot: Pianobot):
        self.bot = bot
        self.logger = getLogger('tasks')

    async def start_tasks(self) -> None:
        self._loop_30s.start()
        self._loop_1m.start()
        self._loop_5m.start()

    async def _run_task(
        self, task: Callable[[Pianobot], Coroutine[Any, Any, None]], name: str
    ) -> None:
        start = perf_counter()
        await task(self.bot)
        self.logger.debug('%s task finished in %s seconds', name, perf_counter() - start)

    @loop(seconds=30)
    async def _loop_30s(self) -> None:
        if self.bot.enable_tracking is True:
            await self._run_task(territories, 'Territory')
        await self._run_task(worlds, 'World')
        await self._run_task(players, 'Player')

    @loop(seconds=60)
    async def _loop_1m(self) -> None:
        await self._run_task(member_activity, 'Member Activity')
    
    @loop(seconds=120)
    async def _loop_2m(self) -> None:
        await self._run_task(guild_raids, 'Guild Raids') 

    @loop(seconds=300)
    async def _loop_5m(self) -> None:
        await self._run_task(guild_activity, 'Guild Activity')
        await self._run_task(guild_awards, 'Guild Awards')
        await self._run_task(guild_xp, 'Guild XP')
        await self._run_task(members, 'Member')

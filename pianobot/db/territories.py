from datetime import datetime

from pianobot.db import Connection


class Territory:
    def __init__(self, name: str, guild: str, acquired: datetime) -> None:
        self._name = name
        self._guild = guild
        self._acquired = acquired

    @property
    def name(self) -> str:
        return self._name

    @property
    def guild(self) -> str:
        return self._guild

    @property
    def acquired(self) -> datetime:
        return self._acquired


class TerritoryTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def add(self, name: str, guild: str | None, acquired: datetime) -> None:
        await self._con.execute(
            'INSERT INTO territories VALUES ($1, $2, $3) ON CONFLICT (name) DO NOTHING', name, guild, acquired
        )

    async def get_all(self) -> list[Territory]:
        result = await self._con.query('SELECT name, guild, acquired FROM territories')
        return [Territory(row[0], row[1], row[2]) for row in result]

    async def remove(self, name: str) -> None:
        await self._con.execute('DELETE FROM territories WHERE name = $1', name)

    async def update(self, name: str, guild: str | None, acquired: datetime) -> None:
        await self._con.execute('UPDATE territories SET guild = $1, acquired = $2 WHERE name = $3', guild, acquired, name)

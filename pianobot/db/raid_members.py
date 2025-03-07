from uuid import UUID

from pianobot.db import Connection


class RaidMemberTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def get_all(self) -> dict[UUID, int]:
        result = await self._con.query('SELECT uuid, xp FROM raid_members')
        return {row[0]: row[1] for row in result}

    async def add(self, uuid: UUID, xp: int) -> None:
        await self._con.execute('INSERT INTO raid_members (uuid, xp) VALUES ($1, $2)', uuid, xp)

    async def remove(self, uuid: UUID) -> None:
        await self._con.execute('DELETE FROM raid_members WHERE uuid = $1', uuid)

    async def update_xp(self, uuid: UUID, xp: int) -> None:
        await self._con.execute('UPDATE raid_members SET xp = $1 WHERE uuid = $2', xp, uuid)

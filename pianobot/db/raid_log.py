from logging import getLogger
from uuid import UUID

from asyncpg import NotNullViolationError

from pianobot.db import Connection


class RaidLogTable:
    def __init__(self, con: Connection) -> None:
        self._con = con

    async def add(self, uuid: UUID, name: str) -> None:
        try:
            await self._con.execute(
                'INSERT INTO raid_log (uuid, raid_id)'
                ' VALUES ($1, (SELECT id FROM raid_names WHERE name = $2))',
                uuid,
                name
            )
        except NotNullViolationError:
            getLogger('db.raid_log').warning('Failed to add log entry for (%s, %s)', uuid, name)

    async def get_new(self) -> dict[str, int]:
        result = await self._con.query(
            'SELECT m.name, count(*) FROM members m, raid_log l'
            ' WHERE m.uuid = l.uuid'
            ' AND l.timestamp >= (select timestamp from raid_log where raid_id = 1)'
            ' GROUP BY m.name'
        )
        return {row[0]: row[1] for row in result}

    async def reset_new(self) -> None:
        await self._con.execute(
            'UPDATE raid_log SET timestamp = CURRENT_TIMESTAMP WHERE raid_id = 1'
        )
